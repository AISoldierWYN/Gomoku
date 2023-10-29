import pygame
import sys
import math
import time

# 屏幕尺寸
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# ====棋盘配置参数==== #
CHESS_RADIUS = 10 # 棋的半径
CHESS_WIDTH = 1 # 白棋线条粗细

BOARD_LINE_NUMS = 15 # 棋盘的线条数，棋盘是正方形
LINE_INTERVAL = 3 * CHESS_RADIUS # 两条线之间的间隔宽度 = 3 * 棋半径
LINE_LENGTH = (BOARD_LINE_NUMS - 1) * LINE_INTERVAL # 线长 = 线条数 * 2 * 棋半径 + 线条数 * 1 * 间隔， 其中间隔设定等于棋半径
LINE_WIDTH = 2 # 线的粗线宽度
# 棋盘左上角坐标，left,top
BOARD_LEFT = 50
BOARD_TOP = 50
# 棋盘的范围，left top的min max范围
BOARD_LEFT_MIN = BOARD_LEFT
BOARD_LEFT_MAX = BOARD_LEFT_MIN + LINE_LENGTH
BOARD_TOP_MIN = BOARD_TOP
BOARD_TOP_MAX = BOARD_TOP_MIN + LINE_LENGTH
# 白棋：1，黑棋：-1，空白处0
BOARD_MAP_WHITE_CHESS = 1
BOARD_MAP_BLACK_CHESS = -1
BOARD_MAP_NONE = 0
# 白棋方：True，黑棋方：False
WHITE_STEP = True
BLACK_STEP = False
# 5子获胜
SUCCEED_CHESS_NUMS = 5
WHITE_WIN = True
BLACK_WIN = False

# 颜色定义
BOARD_COLOR = (0xE3, 0x92, 0x65)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# 屏幕刷新率
FPS = 30

class CheckerBoard():
    board_map = [[0] * BOARD_LINE_NUMS for _ in range(BOARD_LINE_NUMS)] # 棋盘上存储每个位置棋的内容的map
    user = WHITE_STEP
    user_win = None
    vs_computer = None

    def __init__(self, is_man_vs_computer:bool):
        self.vs_computer = is_man_vs_computer
        # key:index, value:list[0: ///, 1: \\\]
        self.oblique_score_map = {(x, i): [0, 0] for x in [0, BOARD_LINE_NUMS - 1] for i in range(BOARD_LINE_NUMS)}
        # key:index, value:list[0: row line --, 1: col line |]
        self.vertical_score_map = {(i, i): [0, 0] for i in range(BOARD_LINE_NUMS)}
        self.score = self.evaluate_board_score_total()
        self.depth = 2
        pass

    def get_current_score(self):
        return self.score

    def evaluate_board_score_total(self):
        """
        统计当前棋盘分数，不更新
        """
        total_score = 0
        for score in self.oblique_score_map.values():
            total_score += score[0] + score[1]
        for score in self.vertical_score_map.values():
            total_score += score[0] + score[1]
        # print(total_score) # debug log
        return total_score
    
    def update_score_map_by_index(self, index):
        """
        通过落子位置更新棋盘评估分数
        index: 落子位置
        """
        i, j = index
        vertical_update_index_1 = (i, i, 0)
        vertical_update_index_2 = (j, j, 1)
        oblique_update_index_1 = None
        oblique_update_index_2 = None
        if j < i:
            if i + j >= BOARD_LINE_NUMS:
                oblique_update_index_1 = (BOARD_LINE_NUMS - 1, i + j - (BOARD_LINE_NUMS - 1), 0)
                oblique_update_index_2 = (BOARD_LINE_NUMS - 1, (BOARD_LINE_NUMS - 1) + j - i, 1)
            else:
                oblique_update_index_1 = (0, i + j, 0)
                oblique_update_index_2 = (BOARD_LINE_NUMS - 1, (BOARD_LINE_NUMS - 1) + j - i, 1)
        elif j >= i:
            if i + j >= BOARD_LINE_NUMS:
                oblique_update_index_1 = (BOARD_LINE_NUMS - 1, i + j - (BOARD_LINE_NUMS - 1), 0)
                oblique_update_index_2 = (0, j - i, 1)
            else:
                oblique_update_index_1 = (0, i + j, 0)
                oblique_update_index_2 = (0, j - i, 1)
        self.update_vertical_score_by_index(vertical_update_index_1)
        self.update_vertical_score_by_index(vertical_update_index_2)
        self.update_oblique_score_by_index(oblique_update_index_1)
        self.update_oblique_score_by_index(oblique_update_index_2)
        return self.score

    def update_vertical_score_by_index(self, vertical_index):
        i, j, k = vertical_index[0], vertical_index[1], vertical_index[2]
        direction = (0, 1) if k == 0 else (1, 0)
        start_i, start_j= i, j # 更新起点的目的是为了在遍历这一行棋子时，始终想从边上开始遍历
        if direction[0] == 0 and direction[1] == 1:
            # 横向的
            start_j = 0
        elif direction[0] == 1 and direction[1] == 0:
            # 纵向的
            start_i = 0
        # 更新对应的vertical_score_map以及总的score
        self.score -= self.vertical_score_map[(i, j)][k]
        self.vertical_score_map[(i, j)][k] = self.calculate_score(start_i, start_j, direction)
        self.score += self.vertical_score_map[(i, j)][k]
    
    def update_oblique_score_by_index(self, oblique_index):
        i, j, k = oblique_index[0], oblique_index[1], oblique_index[2]
        if i == 0:
            direction = (1, -1) if k == 0 else (1, 1)
        elif i == BOARD_LINE_NUMS - 1:
            direction = (-1, 1) if k == 0 else (-1, -1)
        # 更新对应的oblique_score_map以及总的score
        self.score -= self.oblique_score_map[(i, j)][k]
        self.oblique_score_map[(i, j)][k] = self.calculate_score(i, j, direction)
        self.score += self.oblique_score_map[(i, j)][k]
    
    def calculate_score(self, i, j, direction):
        cur_i, cur_j, score = i, j, 0
        left_block = True
        consequent_white_chess_nums = 0
        consequent_black_chess_nums = 0
        length = 0
        while 0 <= cur_i < BOARD_LINE_NUMS and 0 <= cur_j < BOARD_LINE_NUMS:
            if self.board_map[cur_i][cur_j] == BOARD_MAP_NONE:
                # 遇到空白处
                if consequent_black_chess_nums != 0 and consequent_white_chess_nums == 0:
                    # 自空白处碰到的黑子有几个，需要统计下黑子数目
                    score += self.checkup_score(True, consequent_black_chess_nums, 1 if left_block else 0)
                    consequent_black_chess_nums = 0
                elif consequent_black_chess_nums == 0 and consequent_white_chess_nums != 0:
                    score += self.checkup_score(False, consequent_white_chess_nums, 1 if left_block else 0)
                    consequent_white_chess_nums = 0
                left_block = False
            elif self.board_map[cur_i][cur_j] == BOARD_MAP_BLACK_CHESS:
                # 遇到黑棋
                if consequent_white_chess_nums != 0:
                    # 之前有白棋
                    score += self.checkup_score(False, consequent_white_chess_nums, 2 if left_block else 1)
                    consequent_white_chess_nums = 0
                    left_block = True # 左边为白棋
                consequent_black_chess_nums += 1
            elif self.board_map[cur_i][cur_j] == BOARD_MAP_WHITE_CHESS:
                # 遇到白棋
                if consequent_black_chess_nums != 0:
                    # 之前有黑棋
                    score += self.checkup_score(True, consequent_black_chess_nums, 2 if left_block else 1)
                    consequent_black_chess_nums = 0
                    left_block = True # 左边为黑棋
                consequent_white_chess_nums += 1
            cur_i += direction[0]
            cur_j += direction[1]
            length += 1
        
        # 统计遇到边界后的剩余分数，以及根据整体长度判断是否需要调整分数
        if length < 5:
            return 0 # 总长小于5，必不可能连成5子，里面的所有子都不计分数
        else:
            if consequent_black_chess_nums != 0:
                score += self.checkup_score(True, consequent_black_chess_nums, 2 if left_block else 1)
            elif consequent_white_chess_nums != 0:
                score += self.checkup_score(False, consequent_white_chess_nums, 2 if left_block else 1)
        
        if length != BOARD_LINE_NUMS:
            # 斜向的分数，根据斜向长度，等比缩减
            score = score * length // BOARD_LINE_NUMS
        
        return score
        
    
    def checkup_score(self, is_black_chess:bool, nums:int, block_chess_nums:int):
        """
        is_black_chess: 是否是黑棋\n
        nums: 统计的连续棋子数目\n
        block_chess_nums: 该连续棋子两端是否有阻拦，阻拦的个数
        """
        score = 0
        if nums >= 5:
            score = 10000 # 5子 或以上
        elif nums == 4:
            if block_chess_nums == 0:
                score = 4000 # 活4
            elif block_chess_nums == 1:
                score = 2000 # 单4
            elif block_chess_nums == 2:
                score = 0 # 死4
        elif nums == 3:
            if block_chess_nums == 0:
                score = 800 # 活3
            elif block_chess_nums == 1:
                score = 200 # 单3
            elif block_chess_nums == 2:
                score = 0 # 死3
        elif nums == 2:
            if block_chess_nums == 0:
                score = 80 # 活2
            elif block_chess_nums == 1:
                score = 8 # 单2
            elif block_chess_nums == 2:
                score = 0 # 死2
        elif nums == 1:
            if block_chess_nums == 0:
                score = 8 # 活1
            elif block_chess_nums == 1:
                score = 2 # 单1
            elif block_chess_nums == 2:
                score = 0
        else:
            score = 0
        return score if is_black_chess else -1 * score
        

    def make_score_max(self):
        score_now = self.evaluate_board_score()
        max_score = score_now
        max_index0, max_index1 = 0, 0
        for idx0 in range(BOARD_LINE_NUMS):
            for idx1 in range(BOARD_LINE_NUMS):
                # 遍历下一个能下棋的位置
                if self.board_map[idx0][idx1] == BOARD_MAP_NONE:
                    self.board_map[idx0][idx1] = BOARD_MAP_BLACK_CHESS
                    score_current = self.evaluate_board_score()
                    if score_current > max_score:
                        max_score = score_current
                        max_index0, max_index1 = idx0, idx1
                    self.board_map[idx0][idx1] = BOARD_MAP_NONE
        print('score_now:' + str(score_now))
        print('score_next_max:' + str(max_score))
        print((max_index0, max_index1))

    def get_best_move(self):
        best_move = None
        max_eval = -math.inf
        # start_time = time.time()
        for move in self.get_available_moves():
            i, j = move
            self.board_map[i][j] = BOARD_MAP_BLACK_CHESS
            self.update_score_map_by_index((i, j))
            move_eval = self.minimax(self.depth, -math.inf, math.inf, False, (i, j))
            self.board_map[i][j] = BOARD_MAP_NONE
            self.update_score_map_by_index((i, j))
            if move_eval > max_eval:
                max_eval = move_eval
                best_move = move
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print(f"Elapsed time: {elapsed_time} seconds")
        # print(best_move)
        # print("max score:" + str(max_eval))
        return best_move
    
    def minimax(self, depth, alpha, beta, maximizing_player, index):
        if depth == 0 or self.check_win(index):
            return self.get_current_score()
        if maximizing_player:
            # ai player
            max_eval = -math.inf
            for move in self.get_available_moves():
                i, j = move
                self.board_map[i][j] = BOARD_MAP_BLACK_CHESS
                self.update_score_map_by_index((i, j))
                eval = self.minimax(depth - 1, alpha, beta, False, (i, j))
                self.board_map[i][j] = BOARD_MAP_NONE
                self.update_score_map_by_index((i, j))
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # user player
            min_eval = math.inf
            for move in self.get_available_moves():
                i, j = move
                self.board_map[i][j] = BOARD_MAP_WHITE_CHESS
                self.update_score_map_by_index((i, j))
                eval = self.minimax(depth - 1, alpha, beta, True, (i, j))
                self.board_map[i][j] = BOARD_MAP_NONE
                self.update_score_map_by_index((i, j))
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def get_available_moves(self):
        moves = set()
        for i in range(BOARD_LINE_NUMS):
            for j in range(BOARD_LINE_NUMS):
                if self.board_map[i][j] != BOARD_MAP_NONE:
                    moves.update(self.get_availabel_idex_around((i, j)))
        return moves
    
    def get_availabel_idex_around(self, index):
        around_none_place = []
        for i in range(index[0] - 1, index[0] + 2):
            for j in range(index[1] - 1, index[1] + 2):
                if 0 <= i < BOARD_LINE_NUMS and 0 <= j < BOARD_LINE_NUMS and self.board_map[i][j] == BOARD_MAP_NONE:
                    around_none_place.append((i, j))
        return around_none_place
    
    # 检查当前棋盘局势，给出评估值-启发式评估函数
    def evaluate_board_score(self):
        score = 0
        for idx0 in range(BOARD_LINE_NUMS):
            for idx1 in range(BOARD_LINE_NUMS):
                if self.board_map[idx0][idx1] != BOARD_MAP_NONE:
                    for direction in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                        score += self.evaluate_chess_score_in_certain_direction(idx0, idx1, direction)
        return score

    # 计算单个棋子，按照特定方向上的分数，direction为一个元祖，以(0, 0)为中心考虑，为8个方向其中之一
    # [-1, -1]  [-1, 0]  [-1, 1]
    # [0,  -1]  [0,  0]  [0,  1]
    # [1,  -1]  [1,  0]  [1,  1]
    # 这里的方向对应board_map数组下标
    def evaluate_chess_score_in_certain_direction(self, idx0:int, idx1:int, direction:tuple):
        cur_sum = 1
        chess_num = self.board_map[idx0][idx1]
        score = 0
        one_side_block = False
        for step in range(1, 5):
            i, j = idx0 + direction[0] * step, idx1 + direction[1] * step
            if 0 <= i < BOARD_LINE_NUMS and 0 <= j < BOARD_LINE_NUMS:
                if self.board_map[i][j] == chess_num:
                    cur_sum += 1
                elif self.board_map[i][j] != BOARD_MAP_NONE:
                    one_side_block = True
                    break
                else:
                    # TODO:不连续的棋子的处理
                    break
        if cur_sum == 5: #连续5子
            score = 10000
        elif cur_sum == 4: # 连续四子
            if one_side_block:
                # 检查另一端是否有拦截，从idx处往step的反方向检查一子是否为对方玩家棋子
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 0 # 已经封闭的4子
                else:
                    score = 2000 # 单端4子
            else:
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 2000 # 单端4子
                else:
                    score = 5000 # 双端4子
        elif cur_sum == 3:
            if one_side_block:
                # 检查另一端是否有拦截，从idx处往step的反方向检查一子是否为对方玩家棋子
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 0 # 已经封闭的3子
                else:
                    score = 100 # 单端3子
            else:
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 100 # 单端3子
                else:
                    score = 500 # 双端3子
        elif cur_sum == 2:
            if one_side_block:
                # 检查另一端是否有拦截，从idx处往step的反方向检查一子是否为对方玩家棋子
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 0 # 已经封闭的2子
                else:
                    score = 40 # 单端2子
            else:
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 40 # 单端2子
                else:
                    score = 150 # 双端2子
        elif cur_sum == 1:
            if one_side_block:
                # 检查另一端是否有拦截，从idx处往step的反方向检查一子是否为对方玩家棋子
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 0 # 已经封闭的1子
                else:
                    score = 2 # 单端1子
            else:
                if self.check_chess_block_in_certain_direction(idx0, idx1, tuple(-x for x in direction)):
                    score = 2 # 单端1子
                else:
                    score = 5 # 双端1子
        
        # 电脑玩家分数为正，玩家分数为负
        if not self.computer == (chess_num == BOARD_MAP_WHITE_CHESS):
            score = -1 * score
        return score
    
    # one-step block check，检查特定方向一步，看是否被拦截了,True表示被拦截了
    def check_chess_block_in_certain_direction(self, idx0, idx1, direction):
        next_idx0, next_idx1 = idx0 + direction[0], idx1 + direction[1]
        if next_idx0 < 0 or next_idx0 >= BOARD_LINE_NUMS or next_idx1 < 0 or next_idx1 >= BOARD_LINE_NUMS:
            return True
        if self.board_map[next_idx0][next_idx1] != BOARD_MAP_NONE and self.board_map[next_idx0][next_idx1] != self.board_map[idx0][idx1]:
            return True
        return False

    # 棋盘状态刷新绘制
    def flip(self, screen, font):
        screen.fill(BOARD_COLOR)
        left, top = BOARD_LEFT, BOARD_TOP
        for i in range(BOARD_LINE_NUMS):
            text_top = font.render("{}".format(i), True, BLACK)
            screen.blit(text_top, (left + i * LINE_INTERVAL, top - 20))
            screen.blit(text_top, (left - 20, top + i * LINE_INTERVAL))
            self.draw_line(screen, (left + i * LINE_INTERVAL, top), (left + i * LINE_INTERVAL, top + LINE_LENGTH))
            self.draw_line(screen, (left, top + i * LINE_INTERVAL), (left + LINE_LENGTH, top + i * LINE_INTERVAL))
        for i in range(BOARD_LINE_NUMS):
            for j in range(BOARD_LINE_NUMS):
                if self.board_map[i][j] == BOARD_MAP_BLACK_CHESS:
                    self.draw_chess_by_map_index(screen, (i, j), True)
                elif self.board_map[i][j] == BOARD_MAP_WHITE_CHESS:
                    self.draw_chess_by_map_index(screen, (i, j), False)
        
        if not self.user_win:
            if self.user == WHITE_STEP:
                text = font.render('WHITE STEP NOW', True, BLACK)
            else:
                text = font.render('BLACK STEP NOW', True, BLACK)
            screen.blit(text, (50, 550))
        else:
            if self.user_win == WHITE_WIN:
                text = font.render('!!!WHITE USER WIN!!!', True, BLACK)
            else:
                text = font.render('!!!BLACK USER WIN!!!', True, BLACK)
            screen.blit(text, (50, 550))
    
    # 每下一步棋，根据当前的棋的位置index检查一下是否有某一方满足了胜利条件
    def check_win(self, index):
        check_num = BOARD_MAP_WHITE_CHESS if self.user == WHITE_STEP else BOARD_MAP_BLACK_CHESS
        if self.check_horizon(index, check_num):
            return True
        elif self.check_vertical(index, check_num):
            return True
        elif self.check_oblique(index, check_num):
            return True
        else:
            return False
    
    # 水平方向检查
    def check_horizon(self, index, check_num):
        cur_sum = 1
        i, j = index[0], index[1] - 1
        while j >= 0:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            j -= 1
        
        j = index[1] + 1
        while j < BOARD_LINE_NUMS:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            j += 1
        return cur_sum >= SUCCEED_CHESS_NUMS
    
    # 竖直方向检查
    def check_vertical(self, index, check_num):
        cur_sum = 1
        i, j = index[0] - 1, index[1]
        while i >= 0:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i -= 1
        
        i = index[0] + 1
        while i < BOARD_LINE_NUMS:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i += 1
        return cur_sum >= SUCCEED_CHESS_NUMS

    # 斜向检查
    def check_oblique(self, index, check_num):
        # /////
        cur_sum = 1
        i, j = index[0] + 1, index[1] - 1
        while i < BOARD_LINE_NUMS and j >= 0:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i += 1
            j -= 1
        i, j = index[0] - 1, index[1] + 1
        while i >= 0 and j < BOARD_LINE_NUMS:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i -= 1
            j += 1
        if cur_sum >= SUCCEED_CHESS_NUMS:
            return True
        
        # \\\\\
        cur_sum = 1
        i, j = index[0] - 1, index[1] - 1
        while i >= 0 and j >= 0:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i -= 1
            j -= 1
        i, j = index[0] + 1, index[1] + 1
        while i < BOARD_LINE_NUMS and j < BOARD_LINE_NUMS:
            if self.board_map[i][j] == check_num:
                cur_sum += 1
            else:
                break
            i += 1
            j += 1
        return cur_sum >= SUCCEED_CHESS_NUMS

    # 画棋子
    def draw_chess(self, screen, center, isBlack):
        idx0, idx1 = self.calculate_board_map_index_from_center(center)
        if isBlack:
            self.board_map[idx0][idx1] = BOARD_MAP_BLACK_CHESS
            pygame.draw.circle(screen, BLACK, center, CHESS_RADIUS)
        else:
            self.board_map[idx0][idx1] = BOARD_MAP_WHITE_CHESS
            pygame.draw.circle(screen, BLACK, center, CHESS_RADIUS)
            pygame.draw.circle(screen, WHITE, center, CHESS_RADIUS - CHESS_WIDTH)
    
    # 根据map index画棋子
    def draw_chess_by_map_index(self, screen, index, isBlack):
        center = self.calculate_center_from_board_map_index(index)
        if isBlack:
            pygame.draw.circle(screen, BLACK, center, CHESS_RADIUS)
        else:
            pygame.draw.circle(screen, BLACK, center, CHESS_RADIUS)
            pygame.draw.circle(screen, WHITE, center, CHESS_RADIUS - CHESS_WIDTH)
    
    # 根据棋坐标，计算对应的board_map index
    def calculate_board_map_index_from_center(self, center):
        return (center[1] - BOARD_TOP) // LINE_INTERVAL, (center[0] - BOARD_LEFT) // LINE_INTERVAL
    
    # 根据index，计算对应的坐标
    def calculate_center_from_board_map_index(self, index):
        return index[1] * LINE_INTERVAL + BOARD_LEFT, index[0] * LINE_INTERVAL + BOARD_TOP
    
    # 画棋盘线条
    def draw_line(self, screen, start, end):
        pygame.draw.line(screen, BLACK, start, end, 2)

    # 根据用户鼠标位置移动以及点击，在对应棋盘位置画出方框
    # 鼠标点击下去的话，更新对应位置的board_map值，并检查当前是否有玩家获胜
    def draw_user_mouse_position(self, screen, mouse_pos, mouse_pressed):
        left_mouse_pressed = mouse_pressed[0]
        mouse_left, mouse_top = mouse_pos[0], mouse_pos[1]
        if mouse_left > BOARD_LEFT_MAX or mouse_left < BOARD_LEFT_MIN or mouse_top > BOARD_TOP_MAX or mouse_top < BOARD_TOP_MIN:
            return
        
        mouse_left -= BOARD_LEFT
        mouse_top -= BOARD_TOP
        # 当前鼠标所在格子的左上角的坐标
        left, top = (mouse_left // LINE_INTERVAL) * LINE_INTERVAL, (mouse_top // LINE_INTERVAL) * LINE_INTERVAL
        chess_left, chess_top = 0, 0
        if mouse_left < left + CHESS_RADIUS:
            if mouse_top < top + CHESS_RADIUS:
                # 左上角
                chess_left, chess_top = left + BOARD_LEFT, top + BOARD_TOP
            elif mouse_top > top + 2 * CHESS_RADIUS:
                # 左下角
                chess_left, chess_top = left + BOARD_LEFT, top + LINE_INTERVAL + BOARD_TOP
        elif mouse_left > left + 2 * CHESS_RADIUS:
            if mouse_top < top + CHESS_RADIUS:
                # 右上角
                chess_left, chess_top = left + LINE_INTERVAL + BOARD_LEFT, top +BOARD_TOP
            elif mouse_top > top + 2 * CHESS_RADIUS:
                # 右下角
                chess_left, chess_top = left + LINE_INTERVAL + BOARD_LEFT, top + LINE_INTERVAL + BOARD_TOP
        
        if chess_left == 0 or chess_top == 0:
            return
        
        idx0, idx1 = self.calculate_board_map_index_from_center((chess_left, chess_top))
        if self.board_map[idx0][idx1] != 0:
            return
        if not left_mouse_pressed:
            self.draw_rect(screen, (chess_left, chess_top))
        else:
            if self.user == WHITE_STEP:
                self.board_map[idx0][idx1] = BOARD_MAP_WHITE_CHESS
                if self.check_win((idx0, idx1)):
                    self.user_win = WHITE_WIN
                else:
                    self.user = BLACK_STEP
                    if self.vs_computer:
                        ai_move = self.get_best_move()
                        self.board_map[ai_move[0]][ai_move[1]] = BOARD_MAP_BLACK_CHESS
                        self.update_score_map_by_index(ai_move)
                        if self.check_win(ai_move):
                            self.user_win = BLACK_WIN
                        else:
                            self.user = WHITE_STEP
            elif self.user == BLACK_STEP:
                self.board_map[idx0][idx1] = BOARD_MAP_BLACK_CHESS
                if self.check_win((idx0, idx1)):
                    self.user_win = BLACK_WIN
                else:
                    self.user = WHITE_STEP
            self.update_score_map_by_index((idx0, idx1))
    
    # 画方框
    def draw_rect(self, screen, center):
        pygame.draw.rect(screen, BLACK, (center[0] - CHESS_RADIUS, center[1] - CHESS_RADIUS, 2 * CHESS_RADIUS, 2 * CHESS_RADIUS))
        pygame.draw.rect(screen, WHITE, (center[0] - CHESS_RADIUS + LINE_WIDTH, center[1] - CHESS_RADIUS + LINE_WIDTH, 2 * (CHESS_RADIUS - LINE_WIDTH), 2 * (CHESS_RADIUS - LINE_WIDTH)))


# 程序入口
if __name__ == '__main__':
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('五子棋')
    font = pygame.font.SysFont(None, 20)
    user_select = int(input("请选择：1.人机对战 2.人人对战"))
    checkerBoard = CheckerBoard(user_select == 1)

    # 主循环
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print(checkerBoard.get_current_score())
                elif event.key == pygame.K_RETURN:
                    checkerBoard.get_best_move()
                elif event.key == pygame.K_UP:
                    checkerBoard.depth += 1
                    print("depth:" + str(checkerBoard.depth))
                elif event.key == pygame.K_DOWN:
                    checkerBoard.depth -= 1
                    print("depth:" + str(checkerBoard.depth))
        # 画棋盘
        checkerBoard.flip(screen, font)
        
        # 获取鼠标输入位置并显示
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        checkerBoard.draw_user_mouse_position(screen, mouse_pos, mouse_pressed)

        # 屏幕刷新
        pygame.display.flip()
        clock.tick(FPS)