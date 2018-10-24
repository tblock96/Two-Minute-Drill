## Route choosing/running

# First screen: Choose where to line up receiver

# Second: Choose route pattern

# Third: Run Play, choose when/where to throw

import pygame as pg
from pygame.locals import *
import math, sys

SPEED = 20 # px / s
ACCEL = 0.8 # time constant for exponential acceleration
FIELD_WIDTH = 500 # px
HEIGHT = 700
THROW_SPEED = 70 # px / s
THROW_ACC = 0.9 # (1-err)/length of throw
GRASS = ((50,200,120))
NUM_RUNNERS = 3
FAST_THROW_TIME = 0.5
TIME_SCALE = 1.5
PX_PER_YD = 25
END_ZONE = 110
STARTING_YD = 75
DOWNS = 3
MAN_BUFF = 20

def get_dist(r1, r2):
    x1, y1 = r1
    x2, y2 = r2
    return math.hypot(x2-x1, y2-y1)

def get_direction(r1, r2):
    x1, y1 = r1
    x2, y2 = r2
    return math.atan2(y2-y1, x2-x1)

class Runner(pg.sprite.Sprite):

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((10,10))
        self.image.fill(GRASS)
        pg.draw.line(self.image,(0,0,0),(0,0),(10,10),2)
        pg.draw.line(self.image,(0,0,0),(10,0),(0,10),2)
        self.thrown = 0
        self.location = [0,0]
        self.speed = [0,0]
        self.route = [] # Will become a list of locations
        self.actions = [] # Will become a list of integers
            # 0 -> stop here
            # 1 -> run straight after this
            # 2 -> breakdown at this point
            # 3 -> sprint through this point
    
    def update(self, time):
        if len(self.route) > 0:
            desired_speed = SPEED * \
                (1-(self.actions[0]%2==0) * \
                (get_dist(self.location,self.route[0])< \
                ((1-0.5*self.thrown)/ACCEL*(self.speed[0]**2 + self.speed[1]**2)**0.5)))
            # print("Desired speed %f" %desired_speed)
            desired_dir = get_direction(self.location, self.route[0])
            # print("Desired dir %f" %desired_dir)
            v_targ = [
                desired_speed*math.cos(desired_dir),
                desired_speed*math.sin(desired_dir)]
            v_curr = self.speed
            # print(v_targ)
            dx = v_targ[0] - v_curr[0]
            dy = v_targ[1] - v_curr[1]
            
            diff_x = (dx<-SPEED/2)*(dx+SPEED/2) + (dx>SPEED/2)*(dx-SPEED/2)
            diff_y = (dy<-SPEED/2)*(dy+SPEED/2) + (dy>SPEED/2)*(dy-SPEED/2)
            if diff_x != 0: dx = SPEED/2*(2*(dx>0) - 1)
            if diff_y != 0: dy = SPEED/2*(2*(dy>0) - 1)
            dx = dx*(1-ACCEL*time)
            dy = dy*(1-ACCEL*time)
            
            # print("dx, dy: %f, %f" %(dx, dy))
            v_curr[0] = v_targ[0] - dx - diff_x
            v_curr[1] = v_targ[1] - dy - diff_y
            # print(str(v_curr)+'\n')
            if not self.thrown:
                if get_dist(self.location, self.route[0]) < 5:
                    self.route = self.route[1:]
                    self.actions = self.actions[1:]
        self.location[0] += self.speed[0]*time
        self.location[1] += self.speed[1]*time
    
    def set_route(self, rt):
        self.route = rt[0]
        self.location = rt[0][0]
        self.actions = rt[1]
    
    def ball_thrown(self, target, time):
        self.thrown = 1
        self.route = [target]
        self.actions = [0]

class Defender(pg.sprite.Sprite):

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((11,11))
        self.image.fill(GRASS)
        pg.draw.circle(self.image,(0,0,0),(6,6),5,2)
        self.thrown = 0
        self.location = [0,0]
        self.speed = [0,0]
        self.strategy = [-1,0]
        self.get_target_loc = self.get_loc_before_throw
    
    def update(self, time):
        target_loc = self.get_target_loc()
        if self.thrown == 1: desired_speed = SPEED
        else:
            desired_speed = SPEED * \
                (1- \
                (get_dist(self.location,target_loc)< \
                (1/ACCEL*(self.speed[0]**2 + self.speed[1]**2)**0.5)))
        desired_dir = get_direction(self.location, target_loc)
        v_targ = [
            desired_speed*math.cos(desired_dir),
            desired_speed*math.sin(desired_dir)]
        v_curr = self.speed
        # print(v_targ)
        dx = v_targ[0] - v_curr[0]
        dy = v_targ[1] - v_curr[1]
        
        diff_x = (dx<-SPEED/2)*(dx+SPEED/2) + (dx>SPEED/2)*(dx-SPEED/2)
        diff_y = (dy<-SPEED/2)*(dy+SPEED/2) + (dy>SPEED/2)*(dy-SPEED/2)
        if diff_x != 0: dx = SPEED/2*(2*(dx>0) - 1)
        if diff_y != 0: dy = SPEED/2*(2*(dy>0) - 1)
        dx = dx*(1-ACCEL*time)
        dy = dy*(1-ACCEL*time)
        
        # print("dx, dy: %f, %f" %(dx, dy))
        v_curr[0] = v_targ[0] - dx - diff_x
        v_curr[1] = v_targ[1] - dy - diff_y
        self.location[0] += self.speed[0]*time
        self.location[1] += self.speed[1]*time
    
    def set_strategy(self, strat):
        self.strategy = strat[0]
        self.location = strat[1]
    
    def ball_thrown(self, target, theta, catchable):
        self.thrown = 1
        self.t_target = target
        self.t_theta = theta
        self.t_catchable = catchable
        self.get_target_loc = self.get_loc_after_throw
    
    def get_loc_before_throw(self):
        target, dir = self.strategy
        if target == -1: # Zone
            centre = dir
            min_dist = HEIGHT/3
            found = 0
            for r in r_list:
                dist = get_dist(centre, r.location)
                if dist < min_dist:
                    min_dist = dist
                    found = r
            if found == 0: return centre
            return [found.location[0]+found.speed[0]*4-self.speed[0],
                found.location[1]+found.speed[1]*4-self.speed[1]-MAN_BUFF/4]
        return [r_list[target].location[0]+r_list[target].speed[0]*4-self.speed[0]*2+MAN_BUFF*math.cos(dir),
            r_list[target].location[1]+r_list[target].speed[1]*4+-self.speed[1]*2+MAN_BUFF*math.sin(dir)]
    
    def get_loc_after_throw(self):
        return [self.t_target[0]-self.t_catchable/2*math.cos(self.t_theta),
                self.t_target[1]-self.t_catchable/2*math.sin(self.t_theta)]    
    
def get_route():
    lis = [[FIELD_WIDTH/2,HEIGHT-5]]
    act = [3]
    btn_pos = []
    choosing = 0
    while act[-1] > 1:
        CLOCK.tick(30)
        mx, my = pg.mouse.get_pos()
        for e in pg.event.get():
            if e.type == QUIT:
                sys.exit()
            if e.type == MOUSEBUTTONDOWN:
                if choosing:
                    if mx >= btn_pos[0] and mx <= btn_pos[0]+150 \
                    and my >= btn_pos[1]+10 and my < btn_pos[1]+90:
                        choosing = 0
                        act.append(int((my-btn_pos[1]-10)/20))
                        screen.blit(bg,(0,0))
                        for i in range(1,len(lis)):
                            pg.draw.line(screen,(200,0,0),lis[i-1],lis[i])
                    pg.display.flip()
                else:
                    choosing = 1
                    if len(lis) == 1: lis[0][0] = mx
                    lis.append([mx,my])
                    btn_pos = (min(mx+3,FIELD_WIDTH-160),min(my+3,HEIGHT-110))
                    screen.blit(button,btn_pos)
                    pg.display.flip()
    return lis, act

def get_strategy():
    done = clicked = 0
    while not done:
        CLOCK.tick(30)
        for e in pg.event.get():
            if e.type == QUIT:
                sys.exit()
            if e.type == MOUSEBUTTONDOWN:
                mx, my = pg.mouse.get_pos()
                min_dist = 2*PX_PER_YD
                target = -1
                for i in range(len(r_list)):
                    r = r_list[i]
                    dist = get_dist([mx,my],r.location)
                    if dist < min_dist:
                        min_dist = dist
                        target = i
                clicked = 1     # Ensures we don't pick up a click from a different function
            if e.type == MOUSEBUTTONUP and clicked:
                mx2, my2 = pg.mouse.get_pos()
                direction = math.atan2(my2-my, mx2-mx)
                done = 1
    # Now to sort directions and closest people into how to defend
    # In other words, how to define a strategy
    if target == -1: return [-1, [mx,my]], [mx,my]
    return [target, direction], [mx, my]
                
    
if __name__ == '__main__':
    pg.init()
    pg.font.init()
    
    FONT = pg.font.SysFont('arial', 18)
    screen = pg.display.set_mode((FIELD_WIDTH, HEIGHT))
    bg = pg.Surface((FIELD_WIDTH, HEIGHT))
    bg.fill(GRASS)
    
    button = pg.Surface((150,100))
    button.fill((200,200,200))
    button.blit(FONT.render('Stop Here',0,(0,0,0)),(10,10))
    button.blit(FONT.render('Run Straight [STOP]',0,(0,0,0)),(10,30))
    button.blit(FONT.render('Break Down', 0,(0,0,0)),(10,50))
    button.blit(FONT.render('Sprint Through', 0,(0,0,0)),(10,70))
    CLOCK = pg.time.Clock()
    ball = pg.Surface((7,7))
    ball.fill(GRASS)
    pg.draw.circle(ball, (100,100,10),(4,4),3)
    ball_loc = [FIELD_WIDTH/2, HEIGHT-2]
    
    done = 0
    yard_line = STARTING_YD
    down = 1
    first_down = yard_line+10
    
    while done == 0:
        screen.blit(bg,(0,0))
        pg.draw.line(screen,(100,86,25),
            (0,HEIGHT-(first_down-yard_line)*PX_PER_YD),
            (FIELD_WIDTH,HEIGHT-(first_down-yard_line)*PX_PER_YD),4)
        pg.display.flip()
        print("Down: %d -- To Go: %d" %(down, first_down-yard_line))
        print("Yard Line: %d\n" % \
            ((yard_line<(END_ZONE/2))*yard_line+(yard_line>(END_ZONE/2))*(END_ZONE-yard_line)))
        r_list = []
        for i in range(NUM_RUNNERS):
            r_list.append(Runner())
        for r in r_list:
            r.set_route(get_route())
            pg.draw.line(screen,(100,86,25),
                (0,HEIGHT-(first_down-yard_line)*PX_PER_YD),
                (FIELD_WIDTH,HEIGHT-(first_down-yard_line)*PX_PER_YD),4)
            pg.display.flip()
        screen.blit(bg,(0,0))
        for r in r_list:
            screen.blit(r.image, (r.location[0]-5,r.location[1]-5))
        pg.draw.line(screen,(0,0,0),
            (0,HEIGHT-2*PX_PER_YD),(FIELD_WIDTH,HEIGHT-2*PX_PER_YD),2)
        pg.display.flip()
        
        d_list = []
        for i in range(NUM_RUNNERS+2):
            d_list.append(Defender())
        for d in d_list:
            d.set_strategy(get_strategy())
        
        cover = pg.Surface((11,11))
        cover.fill(GRASS)
        CLOCK.tick()
        power = powering = thrown = done = 0
        screen.blit(bg,(0,0))
        
        for k in range(len(r_list)):
            r = r_list[k]
            lis = r.route
            for i in range(1,len(lis)):
                pg.draw.line(screen,
                    (200-int((200/len(r_list))*k),0,int(200/len(r_list)*k)),lis[i-1],lis[i])
        pg.draw.line(screen,(100,86,25),
            (0,HEIGHT-(first_down-yard_line)*PX_PER_YD),(FIELD_WIDTH,HEIGHT-(first_down-yard_line)*PX_PER_YD),4)
        ball_loc = [FIELD_WIDTH/2, HEIGHT-2]
        
        done_pass = 0
        while done_pass == 0:
            for e in pg.event.get():
                if e.type == QUIT:
                    sys.exit()
                if e.type == MOUSEBUTTONDOWN and not thrown:
                    powering = 1
                if e.type == MOUSEBUTTONUP and powering and not thrown:
                    mx, my = pg.mouse.get_pos()
                    start = [FIELD_WIDTH/2, HEIGHT-2]
                    dist = get_dist(start,[mx,my])
                    theta = get_direction(start, [mx,my])
                    if power > FAST_THROW_TIME:
                        speed = THROW_SPEED
                    else: 
                        speed = THROW_SPEED/2.
                    root_arg = speed**4-(9.81**2*dist**2)
                    if root_arg < 0:
                        if power < FAST_THROW_TIME:
                            speed = min(THROW_SPEED,math.sqrt(dist*9.81))
                        dist = speed**2/9.81
                        root_arg = 0
                        mx = start[0]+math.cos(theta)*dist
                        my = start[1]+math.sin(theta)*dist
                    arg = (speed**2-(root_arg)**0.5)/(9.81*dist)
                    zeta = math.atan(arg)
                    catchable = int(10/math.tan(zeta))
                    catch_area = pg.Surface((5,catchable))
                    catch_area.fill((0,0,255))
                    catch_area.set_colorkey((GRASS))
                    catch_area = pg.transform.rotate(catch_area,-theta*180/3.1416+90)
                    size_x, size_y = catch_area.get_size()
                    screen.blit(catch_area,(mx-size_x/2,
                        my-size_y/2))
                    time = speed*math.sin(zeta)/9.81*2*0.5
                    ball_v = dist/time
                    thrown = 1
                    for r in r_list:
                        r.ball_thrown([mx,my], time)
                    for d in d_list:
                        d.ball_thrown([mx,my], theta, catchable)
            if thrown:
                screen.blit(cover, (ball_loc[0]-4, ball_loc[1]-4))
                ball_loc[0] += ball_v*math.cos(theta)*dt/1000.
                ball_loc[1] += ball_v*math.sin(theta)*dt/1000.
                screen.blit(ball, (ball_loc[0]-3.5, ball_loc[1]-3.5))
                if abs(get_dist(ball_loc, [FIELD_WIDTH/2, HEIGHT-2]) - dist) < catchable:
                    for r in d_list:
                        if get_dist(r.location, ball_loc) < 7:
                            done_pass = -1
                    for r in r_list:
                        if get_dist(r.location, ball_loc) < 7:
                            gain = (HEIGHT-ball_loc[1])/PX_PER_YD
                            print("Catch! Gain of %d" %gain)
                            yard_line += gain
                            done_pass = 1

                if get_dist(ball_loc, [FIELD_WIDTH/2, HEIGHT-2]) > dist + catchable:
                    print("No catch")
                    done_pass = 1
            dt = CLOCK.tick(30)*TIME_SCALE
            if powering: power += dt/1000.
            for r in r_list:
                screen.blit(cover, (r.location[0]-5, r.location[1]-5))
                r.update(dt/1000.)
                screen.blit(r.image, (r.location[0]-5, r.location[1]-5))
            for r in d_list:
                screen.blit(cover, (r.location[0]-5, r.location[1]-5))
                r.update(dt/1000.)
                screen.blit(r.image, (r.location[0]-5, r.location[1]-5))
            pg.display.flip()
        if done_pass == -1:
            print("Interception! You lose!")
            done = 1
        if yard_line > first_down:
            first_down = min(yard_line + 10., END_ZONE)
            down = 1
        else:
            if down == DOWNS:
                print("Turnover on Downs! You lose!")
                done = 1
            else:
                down += 1
        if yard_line > END_ZONE:
            print("Touchdown! YOU WIN!!!")
            done = 1