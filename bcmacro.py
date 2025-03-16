import threading
import time
import random
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import messagebox
import pyautogui
import numpy as np
from PIL import Image
from image_utils import *

class Macro_Baram_Cla():
    def __init__(self):
        # 매크로 상태 및 설정
        self.game_region = (520, 110, 1200, 900)
        self.hpmp_cut_region = (1002, 750, 172, 50)
        self.kingq_cut_region = (320, 220, 400, 300)
        self.left_coord_cut_region = (999, 850, 75, 23)
        self.right_coord_cut_region = (1082, 850, 75, 23)

        self.kings_speech = ['무례', '폐하께', '임무', '무서', '어요', '어명이오', '네이놈', '아직', '다시', '취소', '형벌', '받든']
        # self.kingq_wish = ['처녀귀신', '불귀신', '달갈귀신', '달갤귀신']
        self.kingq_wish = ['처녀귀신']
        self.state = {'macro_running': False, 'macro_type':'auto_hunt', 'mode': 'normal', 'kingq':False, 'auto_gongj_heal':'OFF', 'macro_pause':False, 'auto_move':False, 'move_type':'out_palace', 'auto_pilot': False} 
        self.skill_mapping = {
            'mabi' : {'skk':'1', 'delay':0.02, 'direction':keyboard.Key.left},
            'curse' : {'skk':'2', 'delay':0.02, 'direction':keyboard.Key.left},
            'heal': {'skk':'3', 'delay':0.005, 'direction':keyboard.Key.home},
            'attack': {'skk':'4', 'delay':0.2, 'direction':keyboard.Key.left},
            'gongj': {'skk':'5', 'delay':0.05, 'direction':None},
            'attack_chum': {'skk':'6', 'delay':0.5, 'direction':None},
            'poison': {'skk':'7', 'delay':0.02, 'direction':keyboard.Key.left},
            'hellfire': {'skk':'9', 'delay':0.5, 'direction':keyboard.Key.left},
            'boho': {'skk':'x', 'delay':0.1, 'direction':keyboard.Key.home},
            'muzang': {'skk':'z', 'delay':0.1, 'direction':keyboard.Key.home},
            'east':  {'skk':'m', 'delay':0.1, 'direction':'1'},
            'west':  {'skk':'m', 'delay':0.1, 'direction':'2'},
            'south':  {'skk':'m', 'delay':0.1, 'direction':'3'},
            'north':  {'skk':'m', 'delay':0.1, 'direction':'4'},
        }
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        self.mp_thres = 0.6
        self.hp_thres = 0.6
        self.skill_done = 1
        self.bomu_time = time.time() - 999
        self.mabi_time = time.time() - 999
        self.target_monster = 'Nobody'
        
        # GUI 요소 초기화
        self.root = None
        self.start_button = None
        self.stop_button = None
        self.kingq_button = None
        self.auto_gongj_heal_button = None
        self.auto_move_button = None
        self.auto_pilot_button = None

        ## 임시
        self.auto_pilot_state = 0
        
    def _active_skill(self, skill_name, target_iter=1, reset_tap=False, mouse_target=None):
        """스킬 키 동작 수행"""
        if not (type(skill_name) == list):
            skill_name = [skill_name]
        if not (type(target_iter) == list):
            target_iter = [target_iter]
        
        for si, skill_name_ in enumerate(skill_name):
            delay = random.uniform(self.skill_mapping[skill_name_]['delay'], self.skill_mapping[skill_name_]['delay'] + 0.001)
            for target_i in range(target_iter[si]):
                time.sleep(delay)
                if not self.skill_mapping[skill_name_]['skk'].isdigit():
                    self.keyboard_controller.press(keyboard.Key.shift)
                    time.sleep(delay)
                    self.keyboard_controller.press('z')
                    self.keyboard_controller.release('z')
                    self.keyboard_controller.release(keyboard.Key.shift)
                    time.sleep(delay)
                time.sleep(delay)
                self.keyboard_controller.press(self.skill_mapping[skill_name_]['skk'])
                self.keyboard_controller.release(self.skill_mapping[skill_name_]['skk'])
                if mouse_target is None:
                    if self.skill_mapping[skill_name_]['direction'] is None:
                        pass
                    else:
                        if target_i == 0 and si == 0:
                            time.sleep(delay)
                            if reset_tap:
                                self.keyboard_controller.press(keyboard.Key.home)
                                self.keyboard_controller.release(keyboard.Key.home)   
                                time.sleep(delay)
                            self.keyboard_controller.press(self.skill_mapping[skill_name_]['direction'])
                            self.keyboard_controller.release(self.skill_mapping[skill_name_]['direction'])
    
                        time.sleep(delay)
                        self.keyboard_controller.press(keyboard.Key.enter)
                        self.keyboard_controller.release(keyboard.Key.enter)
                        time.sleep(delay)
                        self.keyboard_controller.press(keyboard.Key.esc)
                        self.keyboard_controller.release(keyboard.Key.esc)
                else:
                    time.sleep(delay)
                    pyautogui.moveTo(mouse_target[0], mouse_target[1], duration=self.skill_mapping[skill_name_]['delay'])
                    time.sleep(delay)
                    pyautogui.click()
                    time.sleep(delay)
                    self.keyboard_controller.press(keyboard.Key.enter)
                    self.keyboard_controller.release(keyboard.Key.enter)
                
    def _reset_tap(self):
        """리셋 키 동작 수행"""
        delay = random.uniform(0.01, 0.01 + 0.01)
        time.sleep(delay)
        self.keyboard_controller.release(keyboard.Key.shift)
        for action_key in [keyboard.Key.esc, keyboard.Key.tab, keyboard.Key.home, keyboard.Key.esc]:
            time.sleep(delay)
            self.keyboard_controller.press(action_key)
            self.keyboard_controller.release(action_key)
                
    def _change_direction(self, tap_method='left_right'):
        """방향 전환"""
        for key, value in self.skill_mapping.items():
            if tap_method == 'left_right':
                if value['direction'] == keyboard.Key.left:
                    self.skill_mapping[key]['direction'] = keyboard.Key.right
                elif value['direction'] == keyboard.Key.right:
                    self.skill_mapping[key]['direction'] = keyboard.Key.left
            elif tap_method == 'natural':
                if value['direction'] == keyboard.Key.left:
                    self.skill_mapping[key]['direction'] = keyboard.Key.up
                elif value['direction'] == keyboard.Key.up:
                    self.skill_mapping[key]['direction'] = keyboard.Key.down
                elif value['direction'] == keyboard.Key.down:
                    self.skill_mapping[key]['direction'] = keyboard.Key.right
                elif value['direction'] == keyboard.Key.right:
                    self.skill_mapping[key]['direction'] = keyboard.Key.left
        
    def auto_gongj(self, run=False):
        screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
        screenshot = capture_and_crop(screenshot, self.hpmp_cut_region)
        
        mp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]*3/4))) for x in np.arange(self.mp_thres-0.1, self.mp_thres, 0.005)])
        mp_color_low = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.005)])
        while mp_color < 30:
            self.state['macro_pause'] = True
            if run and self.state['auto_gongj_heal']!='ON':
                self.state['macro_pause'] = False
                raise
            if self.skill_done == 1:
                if mp_color_low < 40:
                    time.sleep(random.uniform(0.04, 0.04 + 0.01))
                    self.keyboard_controller.press(keyboard.Key.ctrl)
                    time.sleep(random.uniform(0.04, 0.04 + 0.01))
                    self.keyboard_controller.press('u')
                    self.keyboard_controller.release('u')
                    self.keyboard_controller.release(keyboard.Key.ctrl)
                    time.sleep(random.uniform(0.04, 0.04 + 0.01))
                self._active_skill(skill_name='gongj', target_iter=1)
                self._active_skill(skill_name='heal', target_iter=1)
                time.sleep(random.uniform(0.1, 0.1 + 0.05))
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                screenshot = capture_and_crop(screenshot, self.hpmp_cut_region)
                mp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]*3/4))) for x in np.arange(self.mp_thres-0.1, self.mp_thres, 0.01)])
                mp_color_low = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.01)])
        self.state['macro_pause'] = False

    def auto_heal(self, run=False):
        screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
        screenshot = capture_and_crop(screenshot, self.hpmp_cut_region)
        hp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]/4))) for x in np.arange(self.hp_thres-0.1, self.hp_thres, 0.005)])
        while hp_color < 30:
            self.state['macro_pause'] = True
            if run and self.state['auto_gongj_heal']!='ON':
                self.state['macro_pause'] = False
                raise
            if self.skill_done == 1:
                for _ in range(5):
                    self._active_skill(skill_name='heal', target_iter=1)
                time.sleep(0.02)
                self.keyboard_controller.press(keyboard.Key.esc)
                self.keyboard_controller.release(keyboard.Key.esc)
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                screenshot = capture_and_crop(screenshot, self.hpmp_cut_region)
                hp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_cut_region[2]),round(self.hpmp_cut_region[3]/4))) for x in np.arange(self.hp_thres-0.1, self.hp_thres, 0.005)])
        self.state['macro_pause'] = False
    
    def auto_bomu(self):
        if time.time() - self.bomu_time > 60:
            self.state['macro_pause'] = True
            if self.skill_done == 1:
                time.sleep(random.uniform(0.02, 0.02 + 0.01))
                self._active_skill(skill_name='muzang', target_iter=2, reset_tap=True)
                self._active_skill(skill_name='boho', target_iter=2, reset_tap=True)
                self.bomu_time = time.time()
                self.state['macro_pause'] = False

    def auto_mabi(self, run=False):
        if time.time() - self.mabi_time > 5:
            self.state['macro_pause'] = True
            if self.skill_done == 1:
                for key, value in self.skill_mapping.items():
                    if value['direction'] in [keyboard.Key.right,keyboard.Key.up,keyboard.Key.down]:
                        self.skill_mapping[key]['direction'] = keyboard.Key.left
                for active_i in range(8):
                    if not self.state['macro_running']:
                        self._reset_tap()
                        raise
                    self._active_skill(skill_name='mabi', target_iter=1, reset_tap=False)
                    if active_i == 3:
                        self._change_direction(tap_method='left_right')
                        self._reset_tap()
                self.mabi_time = time.time()
                self.state['macro_pause'] = False

    def active_spell_auto(self, skill_name, macro_type, target_iter=1, active_iter=1, change_dir=True, auto_bomu=True, auto_mabi=True):
        if change_dir:
            active_iter = round(active_iter/2)

        for active_i in range(active_iter):
            if auto_bomu:
                self.auto_bomu()
            if auto_mabi:
                self.auto_mabi()
            if not self.state['macro_running'] or not self.state['macro_type']==macro_type:
                self._reset_tap()
                time.sleep(random.uniform(0.1, 0.1 + 0.01))
                self.keyboard_controller.press(keyboard.Key.esc)
                self.keyboard_controller.release(keyboard.Key.esc)
                print('macro stop')
                raise
            while self.state['macro_pause']:
                time.sleep(0.1)
            self.skill_done = 0
            self._active_skill(skill_name, target_iter)
            self.skill_done = 1

        if change_dir:
            self._reset_tap()
            self._change_direction()

            for active_i in range(active_iter):
                if auto_bomu:
                    self.auto_bomu()
                if auto_mabi:
                    self.auto_mabi()
                if not self.state['macro_running'] or not self.state['macro_type']==macro_type:
                    self._reset_tap()
                    time.sleep(random.uniform(0.1, 0.1 + 0.01))
                    self.keyboard_controller.press(keyboard.Key.esc)
                    self.keyboard_controller.release(keyboard.Key.esc)
                    print('macro stop')
                    raise
                while self.state['macro_pause']:
                    time.sleep(0.1)
                self.skill_done = 0
                self._active_skill(skill_name, target_iter)
                self.skill_done = 1

    def run_macro(self):
        """매크로 실행 함수"""
        self.bomu_time = time.time() - 999
        self.mabi_time = time.time() - 999
        while self.state['macro_running']:
            if self.state['macro_type'] == 'auto_hunt':
                self.skill_mapping['poison']['delay']=0.015
                self.skill_mapping['curse']['delay']=0.015
                self.skill_mapping['attack_chum']['delay']=0.008
                self.skill_mapping['attack']['delay']=0.02
                macro_type = 'auto_hunt'
                self.active_spell_auto(skill_name='curse', macro_type=macro_type, target_iter=[1], active_iter=10, change_dir=True, auto_bomu=True, auto_mabi=True)
                self.active_spell_auto(skill_name=['poison','attack_chum', 'attack'], macro_type=macro_type, target_iter=[1,1,1], active_iter=30, change_dir=True, auto_bomu=True, auto_mabi=True)        

            elif self.state['macro_type']=='mabi':
                self.skill_mapping['mabi']['delay']=0.02
                macro_type = 'mabi'
                self.active_spell_auto(skill_name=['mabi'], macro_type=macro_type, target_iter=[1], active_iter=10, change_dir=True, auto_bomu=False, auto_mabi=False)

            elif self.state['macro_type']=='curse':
                self.skill_mapping['curse']['delay']=0.005
                macro_type = 'curse'
                self.active_spell_auto(skill_name='curse', macro_type=macro_type, target_iter=[1], active_iter=20, change_dir=True, auto_bomu=True, auto_mabi=True)

            elif self.state['macro_type']=='poison':
                self.skill_mapping['poison']['delay']=0.005
                macro_type = 'poison'
                self.active_spell_auto(skill_name='poison', macro_type=macro_type, target_iter=[1], active_iter=10, change_dir=True, auto_bomu=True, auto_mabi=True)    
                        
    def auto_gongj_heal(self):
        while self.state['auto_gongj_heal']=='ON':
            self.auto_gongj(run=True)
            self.auto_heal(run=True)
            time.sleep(random.uniform(0.05, 0.05 + 0.01))

    def target_move(self, cur_x, cur_y, coordinate_type, target_coordinate):
        avoid_dict = {
            keyboard.Key.left : [[keyboard.Key.down], [keyboard.Key.up], [keyboard.Key.right,keyboard.Key.down],[keyboard.Key.up],[keyboard.Key.right,keyboard.Key.up],[keyboard.Key.down]],
            keyboard.Key.right : [[keyboard.Key.down], [keyboard.Key.up], [keyboard.Key.left,keyboard.Key.down],[keyboard.Key.up],[keyboard.Key.left,keyboard.Key.up],[keyboard.Key.down]],
            keyboard.Key.down : [[keyboard.Key.right], [keyboard.Key.left], [keyboard.Key.up,keyboard.Key.right],[keyboard.Key.left],[keyboard.Key.up,keyboard.Key.right],[keyboard.Key.left]],
            keyboard.Key.up : [[keyboard.Key.right], [keyboard.Key.left], [keyboard.Key.down,keyboard.Key.right],[keyboard.Key.left],[keyboard.Key.down,keyboard.Key.right],[keyboard.Key.left]],
        }
        if coordinate_type == 'x':
            cur = cur_x
        elif coordinate_type == 'y':
            cur = cur_y
        mi = 0
        delay = random.uniform(0.3, 0.4)
        move_dir = keyboard.Key.right
        if type(target_coordinate) != list:
            target_coordinate = [target_coordinate]
        
        while cur < np.min(target_coordinate) or cur > np.max(target_coordinate):
            if not self.state['auto_move']:
                raise
            if cur < np.min(target_coordinate):
                if coordinate_type == 'x':
                    move_dir = keyboard.Key.right
                elif coordinate_type == 'y':
                    move_dir = keyboard.Key.down
            elif cur > np.max(target_coordinate):
                if coordinate_type == 'x':
                    move_dir = keyboard.Key.left
                elif coordinate_type == 'y':
                    move_dir = keyboard.Key.up
            self.keyboard_controller.press(move_dir)
            screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
            (x,y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)

            if cur_x != x or cur_y != y:
                mi = 0
            mi += 1

            while mi >= 8 and ((coordinate_type == 'x' and cur_x == x) or (coordinate_type == 'y' and cur_y == y)):
                for avoid_key_list in avoid_dict[move_dir]:
                    # 방향전환 포함 2회
                    for avoid_key in avoid_key_list:
                        for _ in range(2):
                            if not self.state['auto_move']:
                                raise
                            self.keyboard_controller.release(move_dir)
                            self.keyboard_controller.press(avoid_key)
                            self.keyboard_controller.release(avoid_key)
                            time.sleep(delay)
                    for _ in range(2):
                        self.keyboard_controller.press(move_dir)
                        time.sleep(delay)
                    screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                    (x,y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)
                    if ((coordinate_type == 'x' and cur_x != x) or (coordinate_type == 'y' and cur_y != y)):
                        break
                mi = 0
            cur_x = x
            cur_y = y

            if coordinate_type == 'x':
                cur = cur_x
            elif coordinate_type == 'y':
                cur = cur_y

        self.keyboard_controller.release(move_dir)
        
        return (cur_x, cur_y)

    def auto_move(self):
        delay = random.uniform(0.25, 0.35)
        auto_g = 0
        while self.state['auto_move']:
            screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
            (cur_x, cur_y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)

            if self.state['move_type'] == 'out_palace':
                # 왕궁 나기기
                if self.state['auto_gongj_heal'] == 'ON':
                    self.start_auto_gongj_heal()
                    auto_g = 1
                # (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=9)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=35)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[12,17])  
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=38)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[12,17])
                for _ in range(3):
                    self.keyboard_controller.press(keyboard.Key.down)
                    self.keyboard_controller.release(keyboard.Key.down)
                    time.sleep(delay)
                if auto_g == 1:
                    self.start_auto_gongj_heal()
                self.start_auto_move()

            elif self.state['move_type'] == 'go_palace':
                # 왕궁 복귀
                if self.state['auto_gongj_heal'] == 'ON':
                    self.start_auto_gongj_heal()
                    auto_g = 1
                self._active_skill('north')
                time.sleep(0.5)
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                (cur_x, cur_y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[73,75])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=42)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[73,75])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=58)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=60)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[71,74])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=55)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[72,74])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=53)
                while cur_x > 20:
                    self.keyboard_controller.press(keyboard.Key.up)
                    self.keyboard_controller.release(keyboard.Key.up)
                    time.sleep(delay)
                    screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                    (cur_x, cur_y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=36)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=11)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=12)
                if auto_g == 1:
                    self.start_auto_gongj_heal()
                self.start_auto_move()

            elif self.state['move_type'] == 'go_haunted_house':
                # 흉가 이동
                if self.state['auto_gongj_heal'] == 'ON':
                    self.start_auto_gongj_heal()
                    auto_g = 1
                self._active_skill('south')
                time.sleep(0.5)
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                (cur_x, cur_y) = get_current_coordinate(screenshot, self.left_coord_cut_region, self.right_coord_cut_region)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=[145,147])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=68)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=125)
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='x', target_coordinate=[68,70])
                (cur_x, cur_y) = self.target_move(cur_x, cur_y, coordinate_type='y', target_coordinate=123)
                if auto_g == 1:
                    self.start_auto_gongj_heal()
                self.start_auto_move()

    def change_macro_type(self):
        type_list = ['auto_hunt', 'mabi', 'curse', 'poison']
        idx = type_list.index(self.state['macro_type'])  # 현재 값의 인덱스 찾기
        self.state['macro_type'] = type_list[(idx + 1) % len(type_list)]  # 다음 값으로 순환
    
    def change_move_type(self):
        type_list = ['out_palace', 'go_haunted_house', 'go_palace']
        idx = type_list.index(self.state['move_type'])  # 현재 값의 인덱스 찾기
        self.state['move_type'] = type_list[(idx + 1) % len(type_list)]  # 다음 값으로 순환
                    
    def auto_king_q(self):
        while self.state['kingq']:
            delay = random.uniform(0.01, 0.001)
            auto_g = 0
            if self.state['auto_gongj_heal'] == 'ON':
                auto_g = 1
                self.start_auto_gongj_heal()
            while True:
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                king_coord = image_detection(screenshot, ['./image/king.png'], 0.6, show=False)

                if len(king_coord) == 0:
                    time.sleep(1)
                else:
                    # 첫 번째 좌표로 마우스 이동
                    target_x = self.game_region[0] + king_coord[0][0]
                    target_y = self.game_region[1] + king_coord[0][1]

                    pyautogui.moveTo(target_x, target_y, duration=0.1)  # 마우스 이동 (0.5초 동안 이동)
                    pyautogui.click()
                    pyautogui.moveTo(self.game_region[0], self.game_region[1], duration=0.1)  # 마우스 이동 (0.5초 동안 이동)

                    # 퀘스트 시작
                    for _ in range(20):
                        if not self.state['kingq']:
                            raise
                        extracted_text = extract_text_from_image(self.game_region, cut_region=self.kingq_cut_region, config=r'--oem 1 --psm 6')
                        extracted_text = extracted_text.replace(' ','')
                        print(extracted_text[:10])
                        
                        p = 0
                        for speech in self.kings_speech:
                            if speech in extracted_text:
                                p = 1
                        if p == 0:
                            break
                            
                        if '어명이오!' in extracted_text:
                            self.target_monster = extracted_text.split('!')[1].split('을')[0].strip()
                            break
                        if '지워졌으니' in extracted_text or '받든' in extracted_text:
                            self.target_monster = 'Nobody'
                            break
                            
                        for __ in range(1):
                            self.keyboard_controller.press(keyboard.Key.right)
                            self.keyboard_controller.release(keyboard.Key.right)
                            time.sleep(delay)
                            self.keyboard_controller.press(keyboard.Key.left)
                            self.keyboard_controller.release(keyboard.Key.left)
                            time.sleep(delay)
                        self.keyboard_controller.press(keyboard.Key.enter)
                        self.keyboard_controller.release(keyboard.Key.enter)
                        time.sleep(delay)

                    self.keyboard_controller.press(keyboard.Key.enter)
                    self.keyboard_controller.release(keyboard.Key.enter)

                    if self.target_monster in self.kingq_wish:
                        break
                    
            self.state['kingq'] = False
            self.kingq_button.config(state=tk.NORMAL)
            if auto_g == 1:
                self.start_auto_gongj_heal()

    def auto_pilot(self):
        delay = random.uniform(0.3, 0.4)
        while self.state['auto_pilot']:
            if self.auto_pilot_state == 0:
                # 왕퀘 받기
                self.state['kingq'] = True
                # self.target_monster = 'Nobody'
                self.auto_king_q()
                time.sleep(delay)
                self.state['move_type'] = 'out_palace'
                self.state['auto_move'] = True
                self.auto_move()
                time.sleep(delay)
                self.state['move_type'] = 'go_haunted_house'
                self.state['auto_move'] = True
                self.auto_move()
                time.sleep(delay)
                self._active_skill(skill_name='boho', target_iter=1)
                self._active_skill(skill_name='muzang', target_iter=1)
                time.sleep(delay)
                # for _ in range(2):
                #     self.keyboard_controller.press(keyboard.Key.up)
                #     self.keyboard_controller.release(keyboard.Key.up)
                #     time.sleep(delay)
                self.auto_pilot_state = 1
                self.start_auto_pilot()
                
            elif self.auto_pilot_state == 1:
                # 왕퀘로 복귀
                self.state['move_type'] = 'go_palace'
                self.state['auto_move'] = True
                self.auto_move()
                time.sleep(delay)
                self.auto_pilot_state = 0
                # self.start_auto_pilot()

    def start_macro(self):
        """매크로 시작"""
        if not self.state['macro_running']:
            self.state['macro_running'] = True
            macro = threading.Thread(target=self.run_macro, daemon=True)
            macro.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

    def stop_macro(self):
        """매크로 종료"""
        self.state['macro_running'] = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def start_kingq(self):
        """매크로 시작"""
        if not self.state['kingq']:
            self.state['kingq'] = True
            kqmacro = threading.Thread(target=self.auto_king_q, daemon=True)
            kqmacro.start()
            self.kingq_button.config(state=tk.DISABLED)
        else:
            self.state['kingq'] = False
            self.kingq_button.config(state=tk.NORMAL)
            
    def start_auto_gongj_heal(self):
        """매크로 시작"""
        if self.state['auto_gongj_heal'] == 'OFF':
            self.state['auto_gongj_heal'] = 'ON'
            ghmacro = threading.Thread(target=self.auto_gongj_heal, daemon=True)
            ghmacro.start()
        else:
            self.state['auto_gongj_heal'] = 'OFF'
            self.state['marco_pause'] = False

    def start_auto_move(self):
        if not self.state['auto_move']:
            self.state['auto_move'] = True
            ammacro = threading.Thread(target=self.auto_move, daemon=True)
            ammacro.start()
            self.auto_move_button.config(state=tk.DISABLED)
        else:
            self.state['auto_move'] = False
            self.auto_move_button.config(state=tk.NORMAL)

    def start_auto_pilot(self):
        if not self.state['auto_pilot']:
            self.state['auto_pilot'] = True
            apmacro = threading.Thread(target=self.auto_pilot, daemon=True)
            apmacro.start()
            self.auto_pilot_button.config(state=tk.DISABLED)
        else:
            self.state['auto_pilot'] = False
            for key in ['macro_running', 'kingq', 'macro_pause', 'auto_move', 'auto_pilot']:
                self.state[key] = False
            self.auto_pilot_button.config(state=tk.NORMAL)
                                
    def on_press(self, key):
        """키 입력 감지"""
        try:
            if key.char in ['Q','>']:
                if self.state['macro_running']:
                    self.stop_macro()
                else:
                    self.start_macro()
            elif key.char == 'A':
                self._active_skill(skill_name='boho', target_iter=1)
                self._active_skill(skill_name='muzang', target_iter=1)
            elif key.char == 'P':
                self.start_auto_pilot()

        except AttributeError:
            pass

    def on_release(self, key):
        """키 해제 감지"""
        try:  
            if key.char == 'S':
                self.change_macro_type()

            elif key.char == 'M':
                self.start_auto_move()

            elif key.char == 'N':
                self.change_move_type()

            elif key.char == '{':
                self.start_auto_gongj_heal()
                
            elif key.char == '}':
                self.start_kingq()
                
        except AttributeError:
            pass

    def update_label(self):
        self.type_label.config(text=f"TYPE: {self.state['macro_type']}")  # Label의 텍스트 업데이트
        self.king_label.config(text=f"KING: {self.target_monster}")  # Label의 텍스트 업데이트
        self.gongj_heal_label.config(text=f"A G/H : {self.state['auto_gongj_heal']}")
        self.move_type_label.config(text=f"MOVE : {self.state['move_type']}")
        self.type_label.after(100, self.update_label)  # 1000ms(1초) 후에 다시 실행
                                
    def create_gui(self):
        """GUI 생성"""
        self.root = tk.Tk()
        self.root.title("바클 매크로")
        position_x, position_y = pyautogui.position()
        window_width, window_height = (306, 450)

        self.root.geometry(f"{window_width}x{window_height}+{-0}+{60}")

        label_font = 10
        pad = 1
        bwidth = 27
        
        # Label 위젯 생성
        self.type_label = tk.Label(self.root, text="macro_type", font=("Arial", label_font))
        self.type_label.grid(row=0, column=0, sticky="w", padx=pad, pady=pad)
        
        self.gongj_heal_label = tk.Label(self.root, text="gongj_heal_mode", font=("Arial", label_font))
        self.gongj_heal_label.grid(row=1, column=0, sticky="w", padx=pad, pady=pad)

        self.king_label = tk.Label(self.root, text="king_target_monster", font=("Arial", label_font))
        self.king_label.grid(row=2, column=0, sticky="w", padx=pad, pady=pad)
        
        self.start_button = tk.Button(self.root, text="매크로 시작", command=self.start_macro, width=bwidth, font=("Arial", label_font))
        self.start_button.grid(row=3, column=0, padx=pad, pady=pad)

        self.stop_button = tk.Button(self.root, text="매크로 종료", command=self.stop_macro, width=bwidth, font=("Arial", label_font), state=tk.DISABLED)
        self.stop_button.grid(row=4, column=0, padx=pad, pady=pad)
        
        self.auto_gongj_heal_button = tk.Button(self.root, text="자동 공증/힐", command=self.start_auto_gongj_heal, width=bwidth, font=("Arial", label_font))
        self.auto_gongj_heal_button.grid(row=5, column=0, padx=pad, pady=pad)
        
        self.kingq_button = tk.Button(self.root, text="왕퀘 자동 받기", command=self.start_kingq, width=bwidth, font=("Arial", label_font))
        self.kingq_button.grid(row=6, column=0, padx=pad, pady=pad)

        self.auto_move_button = tk.Button(self.root, text="자동 이동", command=self.start_kingq, width=bwidth, font=("Arial", label_font))
        self.auto_move_button.grid(row=7, column=0, padx=pad, pady=pad)

        self.move_type_label = tk.Label(self.root, text="MOVE", font=("Arial", label_font))
        self.move_type_label.grid(row=8, column=0, sticky="w", padx=pad, pady=pad)

        self.auto_pilot_button = tk.Button(self.root, text="오토파일럿", command=self.start_auto_pilot, width=bwidth, font=("Arial", label_font))
        self.auto_pilot_button.grid(row=9, column=0, padx=pad, pady=pad)
        
        self.update_label()

        # Protocol to handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        
    def on_close(self):
        """Handle window close event."""
        print("Closing the GUI...")
        for key in self.state.keys():
            self.state[key] = False
        self.root.destroy()  # Destroy the GUI window
        
if __name__ == "__main__":
  print('start')
  macrobc = Macro_Baram_Cla()

  listener =  keyboard.Listener(on_press=macrobc.on_press, on_release=macrobc.on_release)
  listener.start()
  macrobc.create_gui()
  listener.stop()
  print('done')