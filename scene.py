"""Build a fresh CoppeliaSim scene using its installed Quadcopter model."""
import math
from pathlib import Path
from sensor_config import MAX_RANGE_M

SNAPSHOT_LUA = '''
-- Added by Indoor Drone Mapping. The original flight controller remains active.
local mappingSensors=nil
local mappingEnvironment=nil
local mappingDrone=nil

function indoorMappingSetup()
    local drone=sim.getObject('/Quadcopter')
    local base=sim.getObject('/Quadcopter/base')
    mappingEnvironment=sim.createCollection(1)
    sim.addItemToCollection(mappingEnvironment,sim.handle_all,-1,0)
    sim.addItemToCollection(mappingEnvironment,sim.handle_tree,drone,1)
    sim.addItemToCollection(mappingEnvironment,sim.handle_single,targetObj,1)
    local floor=sim.getObject('/Floor',{noError=true})
    if floor~=-1 then sim.addItemToCollection(mappingEnvironment,sim.handle_tree,floor,1) end
    mappingDrone=sim.createCollection(1)
    sim.addItemToCollection(mappingDrone,sim.handle_tree,drone,0)
    sim.addItemToCollection(mappingDrone,sim.handle_single,targetObj,1)
    -- Cameras and reference dummies are not physical obstacles. Collection
    -- overrides must not turn those reference points into clearance targets.
    for _,h in ipairs(sim.getObjectsInTree(sim.handle_scene,sim.handle_all,0)) do
        if sim.getObjectType(h)~=sim.sceneobject_shape then
            sim.addItemToCollection(mappingEnvironment,sim.handle_single,h,1)
            sim.addItemToCollection(mappingDrone,sim.handle_single,h,1)
        end
    end
    mappingSensors={}
    for _,name in ipairs({'front','left','back','right'}) do
        local h=sim.getObject('/Quadcopter/base/range_'..name)
        sim.setExplicitHandling(h,1)
        sim.setObjectInt32Param(h,sim.proxintparam_entity_to_detect,mappingEnvironment)
        table.insert(mappingSensors,{handle=h,name=name})
    end
end

function sysCall_sensing()
    if mappingSensors==nil then indoorMappingSetup() end
    local base=sim.getObject('/Quadcopter/base')
    -- A simulated rotating sensor bracket sweeps four short rays. This is not
    -- a long-range sensor, and the drone itself keeps a stable heading.
    local sweep=(sim.getSimulationTime()*0.65) % (math.pi/2)
    for i,sensor in ipairs(mappingSensors) do
        local angle=sweep+(i-1)*math.pi/2
        local c,s=math.cos(angle),math.sin(angle)
        sim.setObjectMatrix(sensor.handle,base,{-s,0,c,0,c,0,s,0,0,1,0,0.04})
        sim.handleProximitySensor(sensor.handle)
    end
end

function indoorMappingSnapshot()
    local b=sim.getObject('/Quadcopter/base')
    local packet={time=sim.getSimulationTime(), position=sim.getObjectPosition(b,sim.handle_world),
        orientation=sim.getObjectOrientation(b,sim.handle_world), rays={}}
    for _,entry in ipairs(mappingSensors) do
        local name=entry.name
        local sensor=entry.handle
        local hit,dist,point,obj=sim.readProximitySensor(sensor)
        local matrix=sim.getObjectMatrix(sensor,sim.handle_world)
        local origin=sim.getObjectPosition(sensor,sim.handle_world)
        local endpoint=sim.multiplyVector(matrix,hit==1 and point or {0,0,__MAX_RANGE__})
        table.insert(packet.rays,{name=name,hit=hit==1,distance=hit==1 and dist or __MAX_RANGE__,
            origin=origin,endpoint=endpoint,object=hit==1 and sim.getObjectAlias(obj,1) or ''})
    end
    -- Geometry checks are evaluation/stop monitors, not planner inputs.
    local contact=sim.checkCollision(mappingDrone,mappingEnvironment)
    local hasDistance,distanceData,pair=sim.checkDistance(mappingDrone,mappingEnvironment)
    packet.collision=contact>0
    packet.surface_clearance=hasDistance>0 and distanceData[7] or -1
    packet.clearance_pair=hasDistance>0 and {sim.getObjectAlias(pair[1],1),sim.getObjectAlias(pair[2],1)} or {}
    return packet
end

function indoorMappingDebug()
    local objects={}
    for _,h in ipairs(sim.getCollectionObjects(mappingEnvironment)) do
        table.insert(objects,sim.getObjectAlias(h,1))
    end
    return objects
end
'''.replace('__MAX_RANGE__',str(MAX_RANGE_M))


def configure(sim):
    """Upgrade an open project in place, preserving walls the user added."""
    if sim.getSimulationState()!=sim.simulation_stopped:
        raise RuntimeError('Stop the simulation before updating its sensor logic.')
    drone=sim.getObject('/Quadcopter')
    descendants=set(sim.getObjectsInTree(drone,sim.handle_all,0))
    for h in sim.getObjectsInTree(sim.handle_scene,sim.sceneobject_shape,0):
        if h not in descendants:
            p=sim.getObjectSpecialProperty(h)
            sim.setObjectSpecialProperty(h,p | sim.objectspecialproperty_detectable_all |
                                         sim.objectspecialproperty_collidable | sim.objectspecialproperty_measurable)
    controller=sim.getObject('/Quadcopter/Script')
    text=sim.getObjectStringParam(controller,sim.scriptstringparam_text)
    if isinstance(text,bytes): text=text.decode('utf-8')
    text=text.split('-- Added by Indoor Drone Mapping.')[0]
    sim.setObjectStringParam(controller,sim.scriptstringparam_text,text+'\n'+SNAPSHOT_LUA)
    return controller


def build(sim, destination):
    if sim.getSimulationState() != sim.simulation_stopped:
        raise RuntimeError('Stop the simulation before building.')
    # Refuse to mix with an existing scene or overwrite a user's work.
    models = [h for h in sim.getObjectsInTree(sim.handle_scene,sim.handle_all,0)
              if sim.getObjectAlias(h) in ('Quadcopter','IndoorMappingRoom')]
    if models:
        raise RuntimeError('Open File > New scene first, then run Build again. Existing scene was preserved.')
    resources = sim.getStringParam(sim.stringparam_resourcesdir)
    model = Path(resources)/'models'/'robots'/'mobile'/'Quadcopter.ttm'
    if not model.is_file():
        raise FileNotFoundError(f'Built-in model missing: {model}. Install the standard CoppeliaSim model library.')
    root = sim.createDummy(0.01)
    sim.setObjectAlias(root,'IndoorMappingRoom')
    environment = sim.createCollection(0)
    specs=[('wall_north',[4.4,.2,1.8],[0,2.1,.9]),('wall_south',[4.4,.2,1.8],[0,-2.1,.9]),
           ('wall_east',[.2,4.4,1.8],[2.1,0,.9]),('wall_west',[.2,4.4,1.8],[-2.1,0,.9])]
    for name,size,position in specs:
        h=sim.createPrimitiveShape(sim.primitiveshape_cuboid,size,0)
        sim.setObjectAlias(h,name)
        sim.setObjectParent(h,root,True)
        sim.setObjectPosition(h,sim.handle_world,position)
        sim.setObjectInt32Param(h,sim.shapeintparam_static,1)
        sim.setObjectInt32Param(h,sim.shapeintparam_respondable,1)
        sim.setObjectSpecialProperty(h,sim.objectspecialproperty_collidable+sim.objectspecialproperty_detectable_all)
        sim.setShapeColor(h,None,sim.colorcomponent_ambient_diffuse,[.66,.72,.79])
        sim.addItemToCollection(environment,sim.handle_single,h,0)
    drone=sim.loadModel(str(model).replace('\\','/'))
    base=sim.getObject('/Quadcopter/base')
    target=sim.getObject('/Quadcopter/target')
    sim.setObjectPosition(target,sim.handle_world,[0,0,.9])
    sim.setObjectOrientation(target,sim.handle_world,[0,0,0])
    for name,yaw in [('front',0),('left',math.pi/2),('back',math.pi),('right',-math.pi/2)]:
        fp=[0.0]*15
        fp[1],fp[12]=MAX_RANGE_M,.025
        sensor=sim.createProximitySensor(sim.proximitysensor_ray,16,0,[0]*8,fp)
        sim.setObjectAlias(sensor,'range_'+name)
        sim.setObjectParent(sensor,base,False)
        c,s=math.cos(yaw),math.sin(yaw)
        # Matrix columns are local X, Y, Z. Sensor detection is along local +Z.
        sim.setObjectMatrix(sensor,base,[-s,0,c,0,c,0,s,0,0,1,0,.04])
        sim.setObjectInt32Param(sensor,sim.proxintparam_entity_to_detect,environment)
    scripts=[h for h in sim.getObjectsInTree(drone,sim.handle_all,0)
             if sim.getObjectType(h)==sim.sceneobject_script]
    if len(scripts)!=1:
        raise RuntimeError(f'Expected one built-in drone script; found {len(scripts)}. Check model version.')
    controller=scripts[0]
    text=sim.getObjectStringParam(controller,sim.scriptstringparam_text)
    if isinstance(text,bytes):
        text=text.decode('utf-8')
    # Remove decorative particle rendering and generation; thrust calculations stay intact.
    text=text.replace('particlesAreVisible=true','particlesAreVisible=false')
    text=text.replace('simulateParticles=true','simulateParticles=false')
    sim.setObjectStringParam(controller,sim.scriptstringparam_text,text+'\n'+SNAPSHOT_LUA)
    sim.setFloatParam(sim.floatparam_simulation_time_step,.05)
    # Frame the room in the standard perspective camera, when available.
    try:
        camera=sim.getObject('/DefaultCamera')
        position=[5.8,-7.2,6.2]
        # +Z is the viewing axis. Construct an orthonormal look-at basis.
        direction=[-position[0],-position[1],.5-position[2]]
        n=math.sqrt(sum(v*v for v in direction)); z=[v/n for v in direction]
        x=[-z[1],z[0],0]; n=math.sqrt(sum(v*v for v in x)); x=[v/n for v in x]
        y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
        sim.setObjectMatrix(camera,sim.handle_world,[x[0],y[0],z[0],position[0],x[1],y[1],z[1],position[1],x[2],y[2],z[2],position[2]])
    except Exception:
        pass
    destination=Path(destination).resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    sim.saveScene(str(destination).replace('\\','/'))
    return {'model':str(model),'scene':str(destination),'controller':controller,'base':base,'target':target}
