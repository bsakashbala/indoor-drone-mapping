"""Build and run indoor drone mapping with wall-aware coverage."""
import argparse
import csv
import json
import math
from pathlib import Path
import socket
import sys
import time

ROOT=Path(__file__).resolve().parent
from mapping import OccupancyGrid
from mission import reference, duration
from sensor_config import MAX_RANGE_M
from navigation import Explorer


class Display:
    def __init__(self):
        import tkinter as tk
        from PIL import ImageTk
        self.tk,self.ImageTk=tk,ImageTk
        self.window=tk.Tk()
        self.window.title('Indoor Drone Mapping | CoppeliaSim')
        self.label=tk.Label(self.window); self.label.pack(padx=16,pady=12)
        self.status=tk.Label(self.window,font=('Segoe UI',11)); self.status.pack(pady=4)
        tk.Label(self.window,text='Dark = occupied   White = free   Gray = unknown   Teal = flight path').pack(pady=(0,12))
        self.closed=False
        self.window.protocol('WM_DELETE_WINDOW',self.close)

    def close(self):
        self.closed=True
        self.window.destroy()

    def update(self,grid,path,t,phase=''):
        if self.closed:
            return
        image=grid.image(path).resize((560,560),resample=0)
        self.photo=self.ImageTk.PhotoImage(image)
        self.label.configure(image=self.photo)
        self.status.configure(text=f'Time {t:.1f} s    Range {MAX_RANGE_M:g} m    {phase}')
        self.window.update()


def connection(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=3):
            pass
    except OSError as e:
        raise RuntimeError(f'Cannot reach CoppeliaSim on localhost:{port}. Open CoppeliaSim and enable its ZMQ remote API server.') from e
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient
    client=RemoteAPIClient(host='127.0.0.1',port=port)
    import zmq
    client.socket.setsockopt(zmq.RCVTIMEO,10000)
    client.socket.setsockopt(zmq.SNDTIMEO,10000)
    return client,client.require('sim')


def ideal_packet(t):
    position,yaw=reference(t)
    rays=[]
    for name,offset in [('front',0),('left',math.pi/2),('back',math.pi),('right',-math.pi/2)]:
        dx,dy=math.cos(yaw+offset),math.sin(yaw+offset)
        candidates=[]
        for p,d in zip(position[:2],(dx,dy)):
            if abs(d)>1e-10:
                candidates.append(((2 if d>0 else -2)-p)/d)
        distance=min(candidates)
        hit=distance<=MAX_RANGE_M
        distance=min(distance,MAX_RANGE_M)
        rays.append({'name':name,'hit':hit,'distance':distance,'origin':position[:],
                     'endpoint':[position[0]+distance*dx,position[1]+distance*dy,position[2]]})
    return {'time':t,'position':position,'orientation':[0,0,yaw],'rays':rays}


def analytic_packet(position,t,rectangles=()):
    """One-metre swept rays for offline navigation checks, without physics."""
    rays=[]
    geometry=[(-2.2,-2.0,-2.2,2.2),(2.0,2.2,-2.2,2.2),
              (-2.2,2.2,-2.2,-2.0),(-2.2,2.2,2.0,2.2),*rectangles]
    for i,name in enumerate(('front','left','back','right')):
        angle=t*.65+i*math.pi/2
        direction=[math.cos(angle),math.sin(angle)]
        distance=MAX_RANGE_M; hit=False
        for xmin,xmax,ymin,ymax in geometry:
            lo,hi=-math.inf,math.inf
            for p,d,mn,mx in zip(position[:2],direction,(xmin,ymin),(xmax,ymax)):
                if abs(d)<1e-12:
                    if not mn<=p<=mx: lo,hi=math.inf,-math.inf
                else:
                    a,b=(mn-p)/d,(mx-p)/d
                    lo=max(lo,min(a,b)); hi=min(hi,max(a,b))
            if hi>=max(lo,0) and 0<lo<=distance:
                distance=lo; hit=True
        origin=[position[0],position[1],position[2]+.04]
        rays.append({'name':name,'hit':hit,'distance':distance,'origin':origin,
                     'endpoint':[origin[0]+direction[0]*distance,origin[1]+direction[1]*distance,origin[2]]})
    return {'time':t,'position':position[:],'orientation':[0,0,0],'rays':rays,'collision':False}


def execute(args):
    grid=OccupancyGrid()
    output=Path(getattr(args,'output',None) or ROOT/'output'/('offline' if args.offline else 'coppeliasim'))
    output.mkdir(parents=True,exist_ok=True)
    display=None if args.no_gui else Display()
    sim=None
    simulation_started=False
    t=0.0
    path=[]; errors=[]; heights=[]; rows=0; completed=False
    navigator=Explorer(grid)
    min_clearance=math.inf; collisions=0; phase='Initial sensor sweep'
    failure=None; version=None
    started=time.monotonic()
    csvfile=(output/'telemetry.csv').open('w',newline='',encoding='utf-8')
    fields=['time_s','x_m','y_m','z_m','roll_rad','pitch_rad','yaw_rad','sensor','hit','range_m',
            'origin_x_m','origin_y_m','origin_z_m','end_x_m','end_y_m','end_z_m',
            'target_x_m','target_y_m','target_z_m','surface_clearance_m','phase']
    writer=csv.writer(csvfile); writer.writerow(fields)
    try:
        if not args.offline:
            client,sim=connection(args.port)
            if sim.getSimulationState()!=sim.simulation_stopped:
                raise RuntimeError('Stop the current simulation before running this mission.')
            scene=ROOT/'IndoorDroneMapping.ttt'
            if not scene.is_file():
                raise RuntimeError('Build the scene first: python run.py --build')
            # Never replace an unrelated open scene or its unsaved changes.
            if sim.getObject('/IndoorMappingRoom',{'noError':True}) == -1:
                raise RuntimeError('Open IndoorDroneMapping.ttt in CoppeliaSim, then run again. Current scene preserved.')
            version=sim.getInt32Param(sim.intparam_program_version)
            base=sim.getObject('/Quadcopter/base')
            target=sim.getObject('/Quadcopter/target')
            from scene import configure
            controller=configure(sim)
            sim.setStepping(True)
            sim.startSimulation()
            simulation_started=True
            # Start the stock controller, which detaches its target during init.
            sim.step()
        t=0.0; last_display=-1; desired=[0,0,.9]
        offline_position=[0,0,.9]
        rectangles=[]
        if getattr(args,'layout','empty')=='partition': rectangles=[(-.8,-.6,-2,-.45)]
        while t<args.max_seconds:
            if display and display.closed:
                break
            if args.offline:
                packet=analytic_packet(offline_position,t,rectangles)
            else:
                packet=sim.callScriptFunction('indoorMappingSnapshot',controller)
            pos=packet['position']; ori=packet['orientation']; t=packet['time']
            if packet.get('collision'):
                collisions+=1
                raise RuntimeError('Contact detected. Simulation stopped; partial measurements saved.')
            clearance=packet.get('surface_clearance',-1)
            if clearance>=0: min_clearance=min(min_clearance,clearance)
            if t>8 and (max(abs(pos[0]),abs(pos[1]))>2.2 or not .35<pos[2]<1.6 or max(abs(ori[0]),abs(ori[1]))>.7):
                raise RuntimeError('Flight left the demonstration limits; simulation stopped. Review telemetry before retrying.')
            path.append(pos[:2]); heights.append(pos[2])
            if t>8:
                errors.append(math.dist(pos,desired))
            for ray in packet['rays']:
                if math.dist(ray['origin'],ray['endpoint'])>MAX_RANGE_M+1e-5:
                    raise RuntimeError('Sensor range differs from this project configuration. Reload the updated IndoorDroneMapping.ttt scene.')
                grid.update(ray['origin'],ray['endpoint'],ray['hit'])
                writer.writerow([round(t,4),*pos,*ori,ray['name'],int(ray['hit']),ray['distance'],*ray['origin'],*ray['endpoint'],*desired,clearance,phase])
                rows+=1
            desired,yaw=navigator.update(packet)
            phase=navigator.phase
            if navigator.done:
                completed=True; break
            if display and t-last_display>.5:
                display.update(grid,path,t,phase); last_display=t
            if args.offline:
                dt=.05
                for i in range(3): offline_position[i]+=max(-.15*dt,min(.15*dt,(desired[i]-offline_position[i])*2*dt))
                t+=dt
            else:
                sim.setObjectPosition(target,sim.handle_world,desired)
                sim.setObjectOrientation(target,sim.handle_world,[0,0,yaw])
                sim.step()
            if display:
                time.sleep(max(0,t-(time.monotonic()-started)))
    except Exception as e:
        failure=str(e)
        raise
    finally:
        csvfile.close()
        if sim and simulation_started:
            try:
                sim.stopSimulation()
                deadline=time.monotonic()+10
                while sim.getSimulationState()!=sim.simulation_stopped and time.monotonic()<deadline:
                    sim.step()
                sim.setStepping(False)
            except Exception as stop_error:
                print(f'Could not confirm simulator stopped: {stop_error}',file=sys.stderr)
        if grid.rays:
            grid.save(output,path)
        metrics=grid.metrics()
        metrics.update({'mode':'analytic navigation check without drone physics' if args.offline else 'CoppeliaSim built-in drone physics',
            'coppeliasim_version':version,'completed':completed,'failure':failure,'simulation_seconds':round(t,3),
            'wall_clock_seconds':round(time.monotonic()-started,2),'telemetry_rows':rows,
            'pose_source':'exact simulator pose' if not args.offline else 'analytic kinematic pose',
            'sensor_max_range_m':MAX_RANGE_M,
            'tracking_rms_m':math.sqrt(sum(e*e for e in errors)/len(errors)) if errors else None,
            'navigation':'wall contour preference and reachable coverage viewpoints',
            'navigation_phase':phase,'navigation_plans':navigator.plans,
            'collision_events':collisions,'minimum_surface_clearance_m':min_clearance if math.isfinite(min_clearance) else None,
            'completion_reason':'No unvisited reachable viewpoint with new visible unknown cells' if completed else 'Interrupted or time limit reached',
            'altitude_min_m':min(heights) if heights else None,'altitude_max_m':max(heights) if heights else None})
        (output/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
        print(json.dumps(metrics,indent=2))
        print(f'Outputs: {output}')
        if display and not display.closed:
            display.update(grid,path,t,phase)
            display.status.configure(text=('Coverage complete' if completed else 'Stopped before coverage complete')+' - results saved. Close this window to exit.')
            display.window.mainloop()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',action='store_true',help='Build and save scene in an empty CoppeliaSim scene')
    parser.add_argument('--offline',action='store_true',help='Check mapping with analytic rays; no drone physics')
    parser.add_argument('--no-gui',action='store_true')
    parser.add_argument('--port',type=int,default=23000)
    parser.add_argument('--max-seconds',type=float,default=900)
    parser.add_argument('--output',type=Path,help='Separate results directory for an experiment')
    parser.add_argument('--layout',choices=['empty','partition'],default='empty',help='Offline navigation check layout')
    args=parser.parse_args()
    if args.build:
        from scene import build
        _,sim=connection(args.port)
        print(json.dumps(build(sim,ROOT/'IndoorDroneMapping.ttt'),indent=2))
    else:
        execute(args)


if __name__=='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted. Partial results were saved.')
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr)
        sys.exit(1)
