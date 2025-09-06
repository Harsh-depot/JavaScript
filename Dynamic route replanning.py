import pygame, random, math, heapq, time
from collections import defaultdict, deque

SCREEN_W, SCREEN_H = 1200, 800
GRID_COLS, GRID_ROWS = 6, 4
CELL_W, CELL_H = 140, 140
MARGIN_X, MARGIN_Y = 120, 100

ROAD_BAND = 48
LANE_WIDTH = ROAD_BAND / 2
NUM_CARS = 12
CAR_W, CAR_H = 28, 50
AMB_W, AMB_H = 36, 60
CAR_COLOR = (35,130,255)
AMB_COLORS = [(220,50,50),(255,120,120)]
ROAD_COLOR = (36,36,36)
LANE_MARK_COLOR = (200,200,200)
INTERSECTION_BG = (30,30,30)
BG_COLOR = (20,20,28)
FPS = 60
DT = 1.0/FPS
AMB_SPEED = 220.0
CAR_SPEED = 110.0
SAFE_BUBBLE = 120.0
REPLAN_EVERY_SEC = 0.6
LIGHT_SWITCH_SEC = 6.0
ALPHA_CONGEST = 2.0
FONT_NAME = None


def node_to_world(node):
    c,r = node
    return (MARGIN_X + c*CELL_W, MARGIN_Y + r*CELL_H)

NODES = [(c,r) for r in range(GRID_ROWS) for c in range(GRID_COLS)]
def neighbors(node):
    c,r = node
    for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
        nc,nr = c+dc,r+dr
        if 0<=nc<GRID_COLS and 0<=nr<GRID_ROWS:
            yield (nc,nr)

def edge_key(a,b): return tuple(sorted((a,b)))
def edge_pos(a,b): return node_to_world(a), node_to_world(b)
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])


edge_counts = defaultdict(int)
EDGES = []
for n in NODES:
    for nb in neighbors(n):
        if (n,nb) not in EDGES and (nb,n) not in EDGES:
            EDGES.append((n,nb))
EDGE_LENGTH = {edge_key(a,b):dist(*edge_pos(a,b)) for a,b in EDGES}
def edge_cost(a,b):
    k = edge_key(a,b)
    return EDGE_LENGTH[k]*(1.0+ALPHA_CONGEST*edge_counts.get(k,0))


def heuristic(a,b):
    ax,ay = node_to_world(a)
    bx,by = node_to_world(b)
    return dist((ax,ay),(bx,by))

def astar_path(start,goal):
    open_set=[]
    heapq.heappush(open_set,(0+heuristic(start,goal),0,start,None))
    came={}
    gscore={start:0}
    while open_set:
        f,g,current,parent=heapq.heappop(open_set)
        if current in came: continue
        came[current]=parent
        if current==goal:
            path=[]
            cur=current
            while cur is not None:
                path.append(cur)
                cur=came[cur]
            path.reverse()
            return path
        for nb in neighbors(current):
            tentative_g = g + edge_cost(current,nb)
            if tentative_g < gscore.get(nb,float('inf')):
                gscore[nb] = tentative_g
                heapq.heappush(open_set,(tentative_g+heuristic(nb,goal),tentative_g,nb,current))
    return [start,goal]


class TrafficLight:
    def _init_(self,node):
        self.node=node
        self.state_by_dir={}
        self.timer=0.0
        self.cycle=LIGHT_SWITCH_SEC
        for nb in neighbors(node):
            self.state_by_dir[(nb,node)]='G' if nb[0]==node[0] else 'R'
        self.forced=False
    def step(self,dt):
        if not self.forced:
            self.timer+=dt
            if self.timer>=self.cycle:
                self.timer=0.0
                for k in self.state_by_dir.keys():
                    self.state_by_dir[k]='G' if self.state_by_dir[k]=='R' else 'R'
    def force_green_from(self,from_node):
        self.forced=True
        for k in self.state_by_dir.keys():
            self.state_by_dir[k]='G' if k[0]==from_node else 'R'
    def clear_force(self): self.forced=False
    def color_for_incoming(self,from_node): return self.state_by_dir.get((from_node,self.node),'G')
lights={n:TrafficLight(n) for n in NODES}


class Vehicle:
    def _init_(self,x,y,w,h,color):
        self.x,self.y=x,y
        self.w,self.h=w,h
        self.color=color
        self.vx,self.vy=0.0,0.0
        self.alive=True
    def draw(self,surf):
        rect=pygame.Rect(0,0,self.w,self.h)
        rect.center=(int(self.x),int(self.y))
        pygame.draw.rect(surf,self.color,rect,border_radius=6)
        pygame.draw.rect(surf,(10,10,10),rect,1,border_radius=6)


class Car(Vehicle):
    def _init_(self,start_node,next_node):
        sx,sy=node_to_world(start_node)
        super()._init_(sx,sy,CAR_W,CAR_H,CAR_COLOR)
        self.u=start_node
        self.v=next_node
        self.s=random.uniform(0.0,0.6)
        self.lateral=random.choice([-LANE_WIDTH/3,LANE_WIDTH/3])
        self.speed=CAR_SPEED
        self.goal=random.choice([n for n in NODES if n!=self.u])
        self.path=self.simple_path_to(self.goal)
        self.path_index=0
        self.state='drive'
        self.yielding_counted=False

    def simple_path_to(self,goal):
        q=deque([self.u])
        prev={self.u:None}
        while q:
            cur=q.popleft()
            if cur==goal: break
            for nb in neighbors(cur):
                if nb not in prev:
                    prev[nb]=cur
                    q.append(nb)
        path=[]
        cur=goal
        if cur not in prev: return [self.u,self.v]
        while cur is not None:
            path.append(cur)
            cur=prev[cur]
        path.reverse()
        return path

    def current_edge_key(self): return edge_key(self.u,self.v)
    def world_pos(self):
        ax,ay=node_to_world(self.u)
        bx,by=node_to_world(self.v)
        x=ax+(bx-ax)*self.s
        y=ay+(by-ay)*self.s
        dx,dy=bx-ax,by-ay
        L=math.hypot(dx,dy)+1e-9
        perpx,perpy=-dy/L,dx/L
        return (x+perpx*self.lateral, y+perpy*self.lateral)

    def step(self,dt,amb):
        self.x,self.y=self.world_pos()
        ax,ay=node_to_world(self.u)
        bx,by=node_to_world(self.v)
        d_to_v=math.hypot(bx-self.x,by-self.y)
        stop_for_light=False
        if d_to_v<36:
            light=lights[self.v]
            if light.color_for_incoming(self.u)=='R': stop_for_light=True
        amb_pos=(amb.x,amb.y)
        d_to_amb=math.hypot(self.x-amb_pos[0],self.y-amb_pos[1])
        same_edge=edge_key(self.u,self.v)==amb.edge
        if same_edge and d_to_amb<SAFE_BUBBLE:
            ux,uy=node_to_world(self.u)
            vx,vy=node_to_world(self.v)
            dx,dy=vx-ux,vy-uy
            L=math.hypot(dx,dy)+1e-9
            perp=(-dy/L,dx/L)
            vectx,vecty=self.x-amb_pos[0],self.y-amb_pos[1]
            dot=perp[0]*vectx+perp[1]*vecty
            sign=1.0 if dot>=0 else -1.0
            desired_lat=sign*LANE_WIDTH
            if abs(desired_lat-self.lateral)>4:
                step_lat=math.copysign(min(30*dt,abs(desired_lat-self.lateral)),desired_lat-self.lateral)
                self.lateral+=step_lat
                self.state='yield'
            else: self.state='stopped'
            if self.state in ('yield','stopped'): self.yielding_counted=True
        else:
            self.state='stopped' if stop_for_light else 'drive'
        edge_k=edge_key(self.u,self.v)
        if edge_k in EDGE_LENGTH:
            edge_len=EDGE_LENGTH[edge_k]
            ds=(self.speed*dt)/edge_len if self.state=='drive' else (self.speed*0.25*dt)/edge_len if self.state=='yield' else 0
            self.s+=ds
        else:
            self.path=self.simple_path_to(self.goal)
            self.u=self.path[0]
            self.v=self.path[1] if len(self.path)>1 else self.path[0]
            self.s=0.0
            return
        if self.s>=1.0-1e-5:
            try:
                idx=self.path.index(self.u)
                next_idx=idx+1
                if next_idx>=len(self.path)-1:
                    self.goal=random.choice([n for n in NODES if n!=self.v])
                    self.path=self.simple_path_to(self.goal)
                    next_idx=0
                self.u=self.v
                self.v=self.path[next_idx+1]
                self.s=0.0
                self.lateral*=0.6
            except:
                self.path=self.simple_path_to(self.goal)
                self.u=self.path[0]
                self.v=self.path[1] if len(self.path)>1 else self.path[0]
                self.s=0.0


def path_pixel_length(path_nodes):
    if not path_nodes or len(path_nodes)==1: return 0.0
    total=0.0
    for i in range(len(path_nodes)-1):
        k=edge_key(path_nodes[i],path_nodes[i+1])
        if k in EDGE_LENGTH: total+=EDGE_LENGTH[k]
    return total
def nearest_grid_node(pt):
    best=None;bestd=1e12
    for n in NODES:
        p=node_to_world(n)
        d=(p[0]-pt[0])*2+(p[1]-pt[1])*2
        if d<bestd: best,bestd=n,d
    return best

class Ambulance(Vehicle):
    def _init_(self,start_node,end_node):
        sx,sy=node_to_world(start_node)
        super()._init_(sx,sy,AMB_W,AMB_H,AMB_COLORS[0])
        self.start=start_node
        self.end=end_node
        self.path=astar_path(start_node,end_node)
        self.idx=0
        self.u=self.path[0]
        self.v=self.path[1] if len(self.path)>=2 else self.path[0]
        self.s=0.0
        self.speed=AMB_SPEED
        self.edge=edge_key(self.u,self.v)
        self.flash_t=0.0
        self.last_replan_t=time.time()
        self.initial_path=self.path[:]
        self.initial_len=path_pixel_length(self.initial_path)
    def update_world_pos(self):
        ax,ay=node_to_world(self.u)
        bx,by=node_to_world(self.v)
        self.x=ax+(bx-ax)*self.s
        self.y=ay+(by-ay)*self.s
        self.edge=edge_key(self.u,self.v)
    def step(self,dt):
        if self.edge not in EDGE_LENGTH:
            self.replan_if_needed()
            return
        edge_len=EDGE_LENGTH[self.edge]
        ds=(self.speed*dt)/edge_len
        self.s+=ds
        self.flash_t+=dt*8.0
        if self.s>=1.0-1e-5:
            self.idx+=1
            if self.idx>=len(self.path)-1:
                self.u=self.path[-1]; self.v=self.path[-1]; self.s=0.0
                self.update_world_pos()
                return
            self.u=self.path[self.idx]
            self.v=self.path[self.idx+1]
            self.s=0.0
        self.update_world_pos()
    def replan_if_needed(self):
        now=time.time()
        if now-self.last_replan_t<REPLAN_EVERY_SEC: return
        self.last_replan_t=now
        nearest=nearest_grid_node((self.x,self.y))
        newp=astar_path(nearest,self.end)
        if newp: self.path=newp; self.idx=0; self.u,self.v=self.path[0],self.path[1]; self.s=0.0
    def remaining_length(self):
        return path_pixel_length(self.path[self.idx:])*(1.0-self.s)+0.0


pygame.init()
screen=pygame.display.set_mode((SCREEN_W,SCREEN_H))
pygame.display.set_caption("TrafficOS — Smart Emergency Corridor")
clock=pygame.time.Clock()
FONT=pygame.font.SysFont(FONT_NAME,18)

cars=[]
def spawn_random_car():
    side=random.choice(['top','bottom','left','right'])
    if side=='top': start=(random.randint(0,GRID_COLS-1),0); nb=(start[0],start[1]+1)
    elif side=='bottom': start=(random.randint(0,GRID_COLS-1),GRID_ROWS-1); nb=(start[0],start[1]-1)
    elif side=='left': start=(0,random.randint(0,GRID_ROWS-1)); nb=(start[0]+1,start[1])
    else: start=(GRID_COLS-1,random.randint(0,GRID_ROWS-1)); nb=(start[0]-1,start[1])
    return Car(start,nb)
for _ in range(NUM_CARS): cars.append(spawn_random_car())

ambulance=Ambulance((0,GRID_ROWS-1),(GRID_COLS-1,0))

def refresh_edge_counts():
    edge_counts.clear()
    for c in cars: edge_counts[edge_key(c.u,c.v)]+=1
refresh_edge_counts()

yielded_set=set()
start_time=time.time()


def draw_roads(surf):
    surf.fill(BG_COLOR)
    for node in NODES:
        x,y=node_to_world(node)
        rect=pygame.Rect(0,0,18,18); rect.center=(int(x),int(y))
        pygame.draw.rect(surf,INTERSECTION_BG,rect)
    for a,b in EDGES:
        (ax,ay),(bx,by)=edge_pos(a,b)
        dx,dy=bx-ax,by-ay
        angle=math.atan2(dy,dx)
        half=ROAD_BAND
        ux,uy=-math.sin(angle)*half,math.cos(angle)*half
        corners=[(ax-ux,ay-uy),(ax+ux,ay+uy),(bx+ux,by+uy),(bx-ux,by-uy)]
        pygame.draw.polygon(surf,ROAD_COLOR,corners)
        pygame.draw.line(surf,LANE_MARK_COLOR,(ax,ay),(bx,by),2)

def draw_lights(surf):
    for n,light in lights.items():
        x,y=node_to_world(n)
        offs=[(-12,0),(12,0),(0,-12),(0,12)]
        dirs=[(n[0]-1,n[1]),(n[0]+1,n[1]),(n[0],n[1]-1),(n[0],n[1]+1)]
        for (dx,dy),from_node in zip(offs,dirs):
            if not (0<=from_node[0]<GRID_COLS and 0<=from_node[1]<GRID_ROWS): continue
            col=(0,200,0) if light.color_for_incoming(from_node)=='G' else (200,40,40)
            pygame.draw.circle(surf,col,(int(x+dx),int(y+dy)),6)

def draw_path(surf,path_nodes):
    if not path_nodes or len(path_nodes)<2: return
    pts=[node_to_world(n) for n in path_nodes]
    pygame.draw.lines(surf,(200,80,80),False,pts,3)
    for p in pts: pygame.draw.circle(surf,(200,80,80), (int(p[0]),int(p[1])),4)

def draw_dashboard(surf,amb,yielded_count):
    rect=pygame.Rect(10,10,320,120)
    pygame.draw.rect(surf,(18,18,24),rect)
    pygame.draw.rect(surf,(100,100,100),rect,2)
    eta=amb.remaining_length()/amb.speed if amb.speed>1e-9 else 0.0
    elapsed=time.time()-start_time
    lines=[f"Elapsed: {int(elapsed)}s",
           f"Amb ETA (est): {eta:.1f}s",
           f"Cars yielded (unique): {yielded_count}",
           f"Initial route len: {int(amb.initial_len)} px",
           f"Current path len: {int(amb.remaining_length())} px"]
    for i,l in enumerate(lines): surf.blit(FONT.render(l,True,(220,220,220)),(18,18+i*22))


running=True
last_recount=0.0
while running:
    dt=clock.tick(FPS)/1000.0
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False

    ambulance.replan_if_needed()
    for lt in lights.values(): lt.clear_force()
    for i in range(max(0,ambulance.idx), min(len(ambulance.path),ambulance.idx+3)):
        node=ambulance.path[i]
        if i>0: lights[node].force_green_from(ambulance.path[i-1])
    for lt in lights.values(): lt.step(dt)

    for c in cars: c.step(dt,ambulance)
    if time.time()-last_recount>0.25:
        edge_counts.clear()
        for c in cars: edge_counts[edge_key(c.u,c.v)]+=1
        last_recount=time.time()
    ambulance.step(dt)
    for c in cars:
        if c.yielding_counted: yielded_set.add(c)

    draw_roads(screen)
    draw_path(screen,ambulance.path)
    draw_lights(screen)
    for c in cars: c.draw(screen)
    amb_color=AMB_COLORS[0] if math.sin(ambulance.flash_t)>0 else AMB_COLORS[1]
    ambulance.color=amb_color
    ambulance.draw(screen)
    pygame.draw.circle(screen,(200,50,50,50),(int(ambulance.x),int(ambulance.y)),int(SAFE_BUBBLE),2)
    draw_dashboard(screen,ambulance,len(yielded_set))
    pygame.display.flip()

pygame.quit()
