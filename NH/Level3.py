from Variables import *
from Astar import *
import copy
import random
import time
import sys
import Map
import Luffy
import Marine
import Astar
import Food
pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PacMan")
font = get_font(30)
score = 0
game_bg = pygame.transform.scale(pygame.image.load("images/game_bg.png"),(WIDTH,HEIGHT))


def Euclid_distance(A,B):
    return math.sqrt((A[0]-B[0])**2+(A[1]-B[1])**2)

def MonsterNode(current_pos, orginal_pos):
    return [current_pos,orginal_pos]

def get_neighbors(maze, position):
    neighbors = []
    for dx, dy in [(1, 0), (-1,0), (0, 1), (0, -1)]:
        x, y = position[0] + dx, position[1] + dy
        if (0 <= x < len(maze) and 0 <= y < len(maze[0])and (maze[x][y] in [0,2])):
            neighbors.append((x, y))
    return neighbors

def get_monster_neighbors(maze, position):
    neighbors = []
    for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        x, y = position[0] + dx, position[1] + dy
        if (0 <= x < len(maze) and 0 <= y < len(maze[0])and maze[x][y]!=1):
            neighbors.append((x, y))
    return neighbors
# Tất cả các monster di chuyển ngẫu nhiên.
def MonsterMove(maze,monsters_node,foods, monsters_path):
    maze1 = copy.deepcopy(maze)
    monsters_subpath = []
    for monster_node in monsters_node:
        if monster_node[0] == monster_node[1]: # đi qua các vị trí xung quanh nó
            able_move = get_monster_neighbors(maze,monster_node[0])
            monster_node[0] = random.choice(able_move)
            maze1[monster_node[1][0]][monster_node[1][1]] = 0
            maze1[monster_node[0][0]][monster_node[0][1]] = 3
        else: # Về lại vị trí cũ
            if monster_node[0] in foods:
                maze1[monster_node[0][0]][monster_node[0][1]] = 2
            else:
                maze1[monster_node[0][0]][monster_node[0][1]] = 0
            monster_node[0] = monster_node[1]
            maze1[monster_node[0][0]][monster_node[0][1]] = 3
        monsters_subpath.append(monster_node[0])
    monsters_path.append(monsters_subpath)
    return maze1, monsters_node, monsters_path


# Tầm nhìn của pac man
def get_pacman_visible(maze, pacman_pos):
    list_d = []
    visible = []
    for x in range(-3,4):
        for y in range(-3,4):
            if abs(x) + abs(y) <= 3 and (x != 0 or y != 0):
                list_d.append((x,y))
    for dx, dy in list_d:
        new_x = pacman_pos[0] + dx
        new_y = pacman_pos[1] + dy
        if 0<= new_y<len(maze[0]) and 0<=new_x<len(maze):
            visible.append((new_x,new_y))
    return visible

# Ăn thức ăn
def eatFood(maze,pacman_pos,foods):
    maze1 = copy.deepcopy(maze)
    foods1 = copy.deepcopy(foods)
    x = pacman_pos[0]
    y = pacman_pos[1]
    maze1[x][y] = 0
    foods1.remove(pacman_pos)
    return maze1, foods1

def get_region_neighbor(maze, pacman_pos,neighbor):
    list_d = []
    list_pos = []
    delta_x, delta_y = neighbor[0] - pacman_pos[0], neighbor[1] - pacman_pos[1]
    if delta_x != 0:
        for dx in range(2):
            for dy in range(-2,3):
                if abs(dx) + abs(dy) <= 2:
                    list_d.append((delta_x*dx,dy))
        list_d.append((delta_x*2,0))
    else:
        for dy in range(2):
            for dx in range(-2,3):
                if abs(dx) + abs(dy) <= 2:
                    list_d.append((dx,delta_y*dy))
        list_d.append((0,delta_y*2))
    for dx, dy in list_d:
        new_x = neighbor[0] + dx
        new_y = neighbor[1] + dy
        if 0<= new_y<len(maze[0]) and 0<=new_x<len(maze):
            list_pos.append((new_x,new_y))
    return list_pos
def check_safe_move(pos,monsters_node):
    monsters = [i[0] for i in monsters_node]
    for monster in monsters:
        if Euclid_distance(pos,monster)<=1:
            return False
    return True
def heuristic(maze, pacman_pos, dict_score_maze,foods, pacman_path, monsters_node):
    maze1 = copy.deepcopy(maze)
    neighbors = get_neighbors(maze1, pacman_pos)
    dict_score = {}
    for neighbor in neighbors:
        region_neighbor = get_region_neighbor(maze1,pacman_pos,neighbor)
        score = 0
        for i in region_neighbor:
            if maze1[i[0]][i[1]] == 0: # đường đi
                score -= 1
            elif maze1[i[0]][i[1]] == 2: # food
                distance = Euclid_distance(neighbor,i)
                if distance == 0:
                    if check_safe_move(i,monsters_node):
                        score += 500
                elif distance == 1:
                    score += 80
                else:
                    score += 30
            elif maze1[i[0]][i[1]] == 3: # monster
                distance = Euclid_distance(neighbor,i)
                if distance == 0:
                    score -= 200
                elif distance == 1:
                    score -= 140
                else:
                    score -= 60
        dict_score_maze[neighbor] = score
        count_neighbor = sum([1 for i in pacman_path if i == neighbor])
        count_pacmanpos = sum([1 for i in pacman_path if i == pacman_pos])
        if neighbor in foods and count_neighbor == 0 and count_pacmanpos>=10:
            dict_score_maze[neighbor] += 50
        if neighbor in pacman_path:
            dict_score_maze[neighbor] -= count_neighbor*6
        dict_score[neighbor] = dict_score_maze[neighbor]
    return dict_score, dict_score_maze

def IdentifyStep(maze, pacman_pos, monsters_node, dict_score_maze,foods,pacman_path):
    dict_score, dict_score_maze = heuristic(maze, pacman_pos, dict_score_maze,foods, pacman_path, monsters_node)
    return max(dict_score.items(),key=lambda x:x[1])[0]

def check_wall_monster_around_food(maze,food):
    food_neighbors = []
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        x, y = food[0] + dx, food[1] + dy
        if (0 <= x < len(maze) and 0 <= y < len(maze[0])):
            food_neighbors.append((x, y))
    for neighbor in food_neighbors:
        if maze[neighbor[0]][neighbor[1]] not in [1,3]:
            return False
    return True
def count_wall_monster_around_food(maze,foods):
    count = 0
    for food in foods:
        if check_wall_monster_around_food(maze,food)==True:
            count+=1
    return count
def pre_Level3(maze_in):
    maze_input = copy.deepcopy(maze_in)
    maze = maze_input[0]
    pacman_pos = maze_input[1]
    foods = maze_input[2]
    monsters = maze_input[3]
    monsters_node = [MonsterNode(monster, monster) for monster in monsters]
    pacman_path = [pacman_pos]
    monsters_path = [[i[0] for i in monsters_node]]
    dict_score_maze = {}
    maze1 = copy.deepcopy(maze)
    count = count_wall_monster_around_food(maze,foods)
    while(True):
        if count==len(foods):
            return maze1, pacman_path, monsters_path, 'block',count
        dict_score, dict_score_maze = heuristic(maze1, pacman_pos, dict_score_maze,foods, pacman_path, monsters_node)
        pacman_pos = IdentifyStep(maze1,pacman_pos,monsters_node,dict_score_maze,foods, pacman_path)
        pacman_path.append(pacman_pos)
        maze1, monsters_node, monsters_path = MonsterMove(maze1, monsters_node, foods,monsters_path)
        if pacman_pos in [i[0] for i in monsters_node]:
            return maze1,pacman_path, monsters_path,'dead',count
        if pacman_pos in foods:
            maze1, foods = eatFood(maze1, pacman_pos,foods)
            if not foods:
                return maze1,pacman_path, monsters_path,'alive',count
def Level3(maze_input):
    global score
    maze, pacman_path, monsters_path, status, food_remain = pre_Level3(maze_input)
    foods = maze_input[2]
    print(foods)
    luffy = Luffy.luffy_right
    marines = [Marine.marine_left] * len(monsters_path[0])
    meat = Food.meat
    running = True
    move_count = 0
    screen.blit(game_bg, (0, 0))
    path_i = 0
    victory_check = False
    lost_check = False
    block_check = False
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if block_check:
            victory_state(screen)
            text = get_font(30).render(f"Score: {score}", True, BLACK)
            screen.blit(text, (80, 470))
            text = get_font(30).render(f"Blocked food: {food_remain}", True, BLACK)
            screen.blit(text, (80, 520))
            pygame.display.update()
        elif not victory_check and not lost_check:
            screen.blit(game_bg, (0, 0))
            Map.create_map(maze_input[0], screen, CELL_SIZE)
            if pacman_path[path_i] in foods:
                score += 20
                foods.remove(pacman_path[path_i])
            for food in foods:
                screen.blit(meat, (get_map_pos_y(maze, CELL_SIZE) + food[1] * CELL_SIZE, get_map_pos_x(maze, CELL_SIZE) + food[0] * CELL_SIZE))
            if path_i < len(pacman_path) - 1:
                if pacman_path[path_i][1] < pacman_path[path_i + 1][1]:
                    luffy = Luffy.luffy_right
                elif pacman_path[path_i][1] > pacman_path[path_i + 1][1]:
                    luffy = Luffy.luffy_left
            screen.blit(luffy, (get_map_pos_y(maze, CELL_SIZE) + pacman_path[path_i][1] * CELL_SIZE,
                                get_map_pos_x(maze, CELL_SIZE) + pacman_path[path_i][0] * CELL_SIZE))
            score -= 1
            for monster_index in range(len(monsters_path[path_i])):
                if path_i < len(monsters_path) - 1:
                    if monsters_path[path_i][monster_index][1] < monsters_path[path_i+1][monster_index][1]:
                        marines[monster_index] = Marine.marine_right
                    elif monsters_path[path_i][monster_index][1] > monsters_path[path_i+1][monster_index][1]:
                        marines[monster_index] = Marine.marine_left
                screen.blit(marines[monster_index], (get_map_pos_y(maze, CELL_SIZE) +monsters_path[path_i][monster_index][1] * CELL_SIZE,
                                    get_map_pos_x(maze, CELL_SIZE) + monsters_path[path_i][monster_index][0] * CELL_SIZE))
            if path_i == len(pacman_path)-1 and status == "dead":
                lost_check = True
            if path_i == len(pacman_path)-1 and status == "block":
                block_check = True
            text = font.render(f"Score: {score}", True, BLACK)
            screen.blit(text, (10, 10))
            pygame.display.update()
            time.sleep(0.08)
            path_i += 1
            if foods == []:
                victory_check = True
        elif victory_check:
            victory_state(screen)
            text = get_font(30).render(f"Score: {score}", True, BLACK)
            screen.blit(text, (80, 470))
            text = get_font(30).render(f"Blocked food: {food_remain}", True, BLACK)
            screen.blit(text, (80, 520))
            pygame.display.update()
        elif lost_check:
            lost_state(screen)
            pygame.display.update()
    pygame.quit()
    sys.exit()