import threading
import time
import random
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import messagebox
import pyautogui
import yaml
import pytesseract
import cv2
import numpy as np
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = './Tesseract-OCR/tesseract.exe'


def capture_and_crop(screenshot, crop_area=None):
    """
    화면 캡처 후 특정 영역을 자름
    :param crop_area: 잘라낼 영역 (x, y, width, height)
    :return: 잘라낸 이미지 (NumPy 배열)
    """
    # 화면 캡처
    screenshot_np = np.array(screenshot)
    image = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # OpenCV BGR 포맷으로 변환
    x, y, w, h = crop_area
    cropped_image = image[y:y+h, x:x+w]
    cropped_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    return cropped_image

def merge_close_coordinates(coordinates, threshold=20):
    """
    가까운 좌표들을 병합하는 함수.
    
    :param coordinates: [(x1, y1), (x2, y2), ...] 형식의 좌표 리스트
    :param threshold: 병합할 최대 거리 임계값
    :return: 병합된 좌표 리스트
    """
    if not coordinates:
        return []

    # numpy 배열로 변환
    coords_array = np.array(coordinates)

    # 결과 저장용 리스트
    merged_coords = []

    # 방문 여부 확인 리스트
    visited = [False] * len(coordinates)

    for i, coord in enumerate(coords_array):
        if visited[i]:
            continue

        # 현재 좌표를 기준으로 병합
        close_group = [coord]
        visited[i] = True

        for j, other_coord in enumerate(coords_array):
            if not visited[j]:
                # 유클리드 거리 계산
                distance = np.linalg.norm(coord - other_coord)
                if distance <= threshold:
                    close_group.append(other_coord)
                    visited[j] = True

        # 그룹의 최소 계산
        group_center = np.min(close_group, axis=0)
        merged_coords.append(tuple(group_center))

    return merged_coords



def image_detection(screenshot, image_path_list, confidence=0.8, show=False):
    screenshot_np = np.array(screenshot)  # PIL 이미지를 NumPy 배열로 변환 (BGR 형식)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # RGB → BGR 변환
    
    coordinates = []
    for image_path in image_path_list:
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        h, w = image.shape[:2]  # 높이와 너비 가져오기

        # 템플릿 매칭
        result = cv2.matchTemplate(screenshot_np, image, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)  # 매칭된 위치 추출 (신뢰도 기준)
        coordinate = list(zip(locations[1], locations[0]))
        coordinate = merge_close_coordinates(coordinate, threshold=20)
        for coordinate_ in coordinate:
            # coordinates.append(coordinate_)
            coordinates.append((round(coordinate_[0] + w // 2), round(coordinate_[1] + h // 2)))
        
    if show:
        for pt in coordinates:
            cv2.rectangle(screenshot_np, pt, (pt[0] + 1, pt[1] + 1), (0, 255, 0), 5)
        cv2.imshow('Matches', screenshot_np)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    return coordinates

def extract_text_from_image(region, cut_region=(360,190,290,230), config=r'--oem 1 --psm 6'):
    screenshot = pyautogui.screenshot(region=region, allScreens=True)
    screenshot_cut = capture_and_crop(screenshot, cut_region)
    screenshot_np = np.array(screenshot_cut)
    screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
    extracted_text = pytesseract.image_to_string(screenshot_gray, lang='kor', config=config)
    return extracted_text

  
class Macro_Baram_Cla():
    def __init__(self):
        # 매크로 상태 및 설정
        self.game_region = (802, 80, 960, 720)
        self.hpmp_region = (1606, 683, 136, 40)
        self.kingq_region_cut = (280, 180, 290, 230) 
        self.kings_speech = ['무례', '폐하께', '어요', '명', 'target', '다시', '취소', '형벌']
        self.kingq_wish = ['처녀귀신', '불귀신', '달갈귀신']
        
        self.state = {'macro_running': False, 'macro_type':'auto_hunt', 'mode': 'normal', 'kingq':False, 'auto_gongj_heal':'OFF', 'macro_pause':False}
        self.skill_mapping = {
            'mabi' : {'skk':'1', 'delay':0.03, 'direction':keyboard.Key.left},
            'curse' : {'skk':'2', 'delay':0.03, 'direction':keyboard.Key.left},
            'heal': {'skk':'3', 'delay':0.005, 'direction':keyboard.Key.home},
            'attack': {'skk':'4', 'delay':0.3, 'direction':keyboard.Key.left},
            'gongj': {'skk':'5', 'delay':0.05, 'direction':None},
            'attack_chum': {'skk':'6', 'delay':0.8, 'direction':None},
            'poison': {'skk':'7', 'delay':0.03, 'direction':keyboard.Key.left},
            'boho': {'skk':'x', 'delay':0.1, 'direction':keyboard.Key.home},
            'muzang': {'skk':'z', 'delay':0.1, 'direction':keyboard.Key.home},
            
        }
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        
        self.mp_thres = round(0.5 * self.hpmp_region[2])
        self.hp_thres = round(0.4 * self.hpmp_region[2])
        self.skill_done = 1
        self.bomu_time = time.time() - 999
        self.target_monster = 'Nobody'
        
        # GUI 요소 초기화
        self.root = None
        self.start_button = None
        self.stop_button = None
        self.kingq_button = None
        self.auto_gongj_heal_button = None
        
    def _active_skill(self, skill_name, target_iter=1, reset_tap=False):
        """스킬 키 동작 수행"""
        if not (type(skill_name) == list):
            skill_name = [skill_name]
        if not (type(target_iter) == list):
            target_iter = [target_iter]
        
        for si, skill_name_ in enumerate(skill_name):
            delay = random.uniform(self.skill_mapping[skill_name_]['delay'], self.skill_mapping[skill_name_]['delay'] + 0.01)
            for target_i in range(target_iter[si]):
                time.sleep(delay)
                if not self.skill_mapping[skill_name_]['skk'].isdigit():
                    self.keyboard_controller.press(keyboard.Key.shift)
                    time.sleep(delay)
                    self.keyboard_controller.press('z')
                    self.keyboard_controller.release('z')
                    self.keyboard_controller.release(keyboard.Key.shift)
                    time.sleep(delay)
                time.sleep(random.uniform(0.01, 0.02))
                self.keyboard_controller.press(self.skill_mapping[skill_name_]['skk'])
                self.keyboard_controller.release(self.skill_mapping[skill_name_]['skk'])

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
                
    def _reset_tap(self):
        """리셋 키 동작 수행"""
        delay = random.uniform(0.03, 0.03 + 0.01)
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
        
    def auto_gongj(self, run=False, pause=True):
        screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
        mp_color = screenshot.getpixel((self.mp_thres, round(self.hpmp_region[3]*3/4)))
        mp_color_low = np.mean([screenshot.getpixel((round(1-x * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.01)])
        while mp_color == (0,0,0):
            self.state['macro_pause'] = True
            if run and self.state['auto_gongj_heal']!='ON':
                raise
            if self.skill_done == 1:
                if mp_color_low < 50:
                    time.sleep(0.04)
                    self.keyboard_controller.press(keyboard.Key.ctrl)
                    time.sleep(0.04)
                    self.keyboard_controller.press('u')
                    self.keyboard_controller.release('u')
                    self.keyboard_controller.release(keyboard.Key.ctrl)
                    time.sleep(0.04)
                self._active_skill(skill_name='gongj', target_iter=1)
                self._active_skill(skill_name='heal', target_iter=1)
                screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
                mp_color = screenshot.getpixel((self.mp_thres, round(self.hpmp_region[3]*3/4)))
                mp_color_low = np.mean([screenshot.getpixel((round(1-x * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.01)])
        if not pause:
            self.state['macro_pause'] = False

    def auto_heal(self, run=False):
        screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
        hp_color = screenshot.getpixel((self.hp_thres,round(self.hpmp_region[3]/4)))
        while hp_color == (0,0,0):
            self.state['macro_pause'] = True
            if run and self.state['auto_gongj_heal']!='ON':
                raise
            if self.skill_done == 1:
                for _ in range(5):
                    self._active_skill(skill_name='heal', target_iter=2)
                time.sleep(0.05)
                self.keyboard_controller.press(keyboard.Key.esc)
                self.keyboard_controller.release(keyboard.Key.esc)
                screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
                hp_color = screenshot.getpixel((self.hp_thres,round(self.hpmp_region[3]/4)))
        self.state['macro_pause'] = False
    
    def auto_bomu(self):
        if time.time() - self.bomu_time > 15:
            self._reset_tap()
            self._active_skill(skill_name='boho', target_iter=2)
            self._active_skill(skill_name='muzang', target_iter=2)
            self.bomu_time = time.time()

    def active_spell_auto(self, skill_name, target_iter=1, active_iter=1, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True):
        if change_dir:
            active_iter = round(active_iter/2)
            
        for active_i in range(active_iter):
            if auto_bomu:
                self.auto_bomu()
            if auto_gongj:
                self.auto_gongj()
            if auto_heal:
                self.auto_heal()
            if not self.state['macro_running'] or not self.state['macro_type']=='auto_hunt':
                raise
            self._active_skill(skill_name, target_iter)
            
        self._reset_tap()
        if change_dir:
            self._change_direction()
            for active_i in range(active_iter):
                if auto_bomu:
                    self.auto_bomu()
                if auto_gongj:
                    self.auto_gongj()
                if auto_heal:
                    self.auto_heal()
                if not self.state['macro_running'] or not self.state['macro_type']=='auto_hunt':
                    self._reset_tap()
                    raise
                self._active_skill(skill_name, target_iter)
                
    def active_spell_auto_natural(self, skill_name, target_iter=1, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True):
        if change_dir:
            dirs = ['left', 'up', 'down', 'right']
        else:
            dirs = ['left']
            
        for active_i in dirs:
            if auto_bomu:
                self.auto_bomu()
            if auto_gongj:
                self.auto_gongj()
            if auto_heal:
                self.auto_heal()
            if not self.state['macro_running'] or not self.state['macro_type']=='auto_hunt':
                self._reset_tap()
                raise
            self._active_skill(skill_name, target_iter, reset_tap=True)
            if len(dirs) > 1:
                self._change_direction(tap_method='natural')

    def run_macro(self):
        """매크로 실행 함수"""
        while self.state['macro_running']:
            self.skill_mapping['mabi']['delay']=0.03
            self.skill_mapping['mabi']['curse']=0.03
            self.skill_mapping['mabi']['poison']=0.03
            if self.state['macro_type'] == 'auto_hunt':
                if self.state['mode'] == 'normal': # 일반사냥, 탭 = 좌우
                    self.active_spell_auto(skill_name=['curse', 'mabi'], target_iter=[1,1], active_iter=16, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    for _ in range(4):
                        self.active_spell_auto(skill_name=['poison', 'mabi'], target_iter=[1,1], active_iter=16, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                        self.active_spell_auto(skill_name=['attack', 'mabi'], target_iter=[1,1], active_iter=10, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                        self.active_spell_auto(skill_name=['poison', 'mabi'], target_iter=[1,1], active_iter=16, change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                        self.active_spell_auto(skill_name='attack_chum', target_iter=1, active_iter=4, change_dir=False, auto_bomu=True, auto_gongj=True, auto_heal=True)   
                elif self.state['mode'] == 'chum': # 첨사냥, 탭 = 자연스럽게
                    self.active_spell_auto_natural(skill_name=['curse', 'mabi'], target_iter=[1,1], change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name=['poison', 'mabi'], target_iter=[1,1], change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name='attack_chum', target_iter=1, change_dir=False, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name='attack_chum', target_iter=1, change_dir=False, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name=['poison', 'mabi'], target_iter=[1,1], change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name=['attack', 'mabi'], target_iter=[1,1], change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name=['poison', 'mabi'], target_iter=[1,1], change_dir=True, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name='attack_chum', target_iter=1, change_dir=False, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    self.active_spell_auto_natural(skill_name='attack_chum', target_iter=1, change_dir=False, auto_bomu=True, auto_gongj=True, auto_heal=True)
                    
            elif self.state['macro_type']=='mabi':
                self.skill_mapping['mabi']['delay']=0.005
                # if self.state['mode'] == 'normal': # 일반사냥, 탭 = 좌우
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='mabi':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self._active_skill(skill_name=['mabi'], target_iter=[1])
                    self.skill_done = 1

                self._change_direction()
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='mabi':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self._active_skill(skill_name=['mabi'], target_iter=[1])
                    self.skill_done = 1
                        
            elif self.state['macro_type']=='curse':
                self.skill_mapping['curse']['delay']=0.005
                self.skill_mapping['poison']['delay']=0.005
                self.skill_mapping['mabi']['delay']=0.005
                # if self.state['mode'] == 'normal': # 일반사냥, 탭 = 좌우
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='curse':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self._active_skill(skill_name=['mabi', 'curse', 'poison'], target_iter=[1,1,1])
                    self.skill_done = 1

                self._change_direction()
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='curse':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self._active_skill(skill_name=['mabi','curse', 'poison'], target_iter=[1,1,1])
                    self.skill_done = 1
                        
            elif self.state['macro_type']=='poison':
                self.skill_mapping['curse']['delay']=0.008
                self.skill_mapping['poison']['delay']=0.008
                self.skill_mapping['mabi']['delay']=0.008
                # if self.state['mode'] == 'normal': # 일반사냥, 탭 = 좌우
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='poison':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self.keyboard_controller.press(keyboard.Key.space)
                    self.keyboard_controller.release(keyboard.Key.space)
                    time.sleep(random.uniform(0.03, 0.03 + 0.01))
                    self._active_skill(skill_name=['mabi','curse','poison'], target_iter=[1,1,1])
                    self.keyboard_controller.press(keyboard.Key.space)
                    self.keyboard_controller.release(keyboard.Key.space)
                    time.sleep(random.uniform(0.03, 0.03 + 0.01))
                    self.skill_done = 1

                self._change_direction()
                for active_i in range(5):
                    if not self.state['macro_running'] or not self.state['macro_type']=='poison':
                        self._reset_tap()
                        raise
                    while self.state['macro_pause']:
                        time.sleep(0.1)
                    self.skill_done = 0
                    self.keyboard_controller.press(keyboard.Key.space)
                    self.keyboard_controller.release(keyboard.Key.space)
                    time.sleep(random.uniform(0.03, 0.03 + 0.01))
                    self._active_skill(skill_name=['mabi','curse','poison'], target_iter=[1,1,1])
                    self.keyboard_controller.press(keyboard.Key.space)
                    self.keyboard_controller.release(keyboard.Key.space)
                    time.sleep(random.uniform(0.03, 0.03 + 0.01))
                    self.skill_done = 1
                        
    def auto_gongj_heal(self):
        while self.state['auto_gongj_heal']=='ON':
            self.auto_gongj(run=True)
            self.auto_heal(run=True)
            time.sleep(0.05)
                    
    def auto_king_q(self):
        while self.state['kingq']:
            delay = random.uniform(0.005, 0.001)
            phase = 1
            self.start_auto_gongj_heal()
            while True:
                screenshot = pyautogui.screenshot(region=self.game_region, allScreens=True)
                king_coord = image_detection(screenshot, ['king2.jpg'], 0.8, show=False)

                if len(king_coord) == 0:
                    time.sleep(0.5)
                else:
                    # 첫 번째 좌표로 마우스 이동
                    target_x = round((self.game_region[0] + king_coord[0][0])/0.8)
                    target_y = round((self.game_region[1] + king_coord[0][1])/0.8) - 1350

                    pyautogui.moveTo(target_x, target_y, duration=0.1)  # 마우스 이동 (0.5초 동안 이동)
                    pyautogui.click()
                    pyautogui.moveTo(self.game_region[0]/0.8, self.game_region[1]/0.8-1350, duration=0.1)  # 마우스 이동 (0.5초 동안 이동)

                    extracted_text = extract_text_from_image(self.game_region, cut_region=self.kingq_region_cut, config=r'--oem 1 --psm 6')
                    if self.target_monster in self.kingq_wish:
                        if '받든' in extracted_text:
                            self.target_monster = 'Nobody'
                            self.keyboard_controller.press(keyboard.Key.space)
                            self.keyboard_controller.release(keyboard.Key.space)
                            time.sleep(1)
                            pyautogui.moveTo(target_x, target_y, duration=0.1)  # 마우스 이동 (0.5초 동안 이동)
                            pyautogui.click()
                            pyautogui.moveTo(self.game_region[0]/0.8, self.game_region[1]/0.8-1350, duration=0.1)  # 마우스 이동 (0.5초 동안 이동)
                            extracted_text = extract_text_from_image(self.game_region, cut_region=self.kingq_region_cut, config=r'--oem 1 --psm 6')
                            
                    if phase == 1:
                        for ti, text in enumerate(self.kings_speech[:4]):
                            if not self.state['kingq']:
                              raise
                            while text in extracted_text:
                                if ti == 2:
                                    for _ in range(50):
                                        self.keyboard_controller.press(keyboard.Key.left)
                                        self.keyboard_controller.release(keyboard.Key.left)
                                        time.sleep(delay)
                                if ti == 3:
                                    self.target_monster = extracted_text.split('!')[1].split('을')[0].strip()
                                    self.kings_speech[4] = self.target_monster
                                    phase = 2
                                self.keyboard_controller.press(keyboard.Key.space)
                                self.keyboard_controller.release(keyboard.Key.space)
                                time.sleep(delay)
                                extracted_text = extract_text_from_image(self.game_region, cut_region=self.kingq_region_cut, config=r'--oem 1 --psm 6')

                        self.keyboard_controller.release(keyboard.Key.esc)

                        if self.target_monster in self.kingq_wish:
                            break

                    elif phase == 2:
                        for ti, text in enumerate(self.kings_speech[4:]):
                            if not self.state['kingq']:
                              raise
                            while text in extracted_text:
                                if ti == 1:
                                    for _ in range(50):
                                        self.keyboard_controller.press(keyboard.Key.left)
                                        self.keyboard_controller.release(keyboard.Key.left)
                                        time.sleep(delay)
                                if ti == 3:
                                    self.target_monster = 'Nobody'
                                    phase = 1
                                self.keyboard_controller.press(keyboard.Key.space)
                                self.keyboard_controller.release(keyboard.Key.space)
                                time.sleep(delay)
                                extracted_text = extract_text_from_image(self.game_region, cut_region=self.kingq_region_cut, config=r'--oem 1 --psm 6')        
                    time.sleep(delay)
                    self.keyboard_controller.press(keyboard.Key.esc)
                    self.keyboard_controller.release(keyboard.Key.esc)
                    
            self.state['kingq'] = False
            self.kingq_button.config(state=tk.NORMAL)
            self.start_auto_gongj_heal()

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
                                
    def on_press(self, key):
        """키 입력 감지"""
        try:
            if key.char in ['/']:
                if self.state['macro_running']:
                    self.stop_macro()
                else:
                    self.start_macro()

        except AttributeError:
            pass

    def on_release(self, key):
        """키 해제 감지"""
        try:
            if key.char == 'M':
                if self.state['mode'] == 'normal':
                    self.state['mode'] = 'chum'
                    print(f"mode change: {self.state['mode']}")
                elif self.state['mode'] == 'chum':
                    self.state['mode'] = 'normal'
                    print(f"mode change: {self.state['mode']}")
                    
            elif key.char == '.':
                self._active_skill(skill_name='boho', target_iter=1)
                self._active_skill(skill_name='muzang', target_iter=1)
                    
            elif key.char == 'A':
                self.state['macro_type'] = 'auto_hunt'
                self.stop_macro()
                print(f"macro_type change: {self.state['macro_type']}")
                
            elif key.char == 'O':
                self.state['macro_type'] = 'mabi'
                self.stop_macro()
                print(f"macro_type change: {self.state['macro_type']}")
                
            elif key.char == 'K':
                self.state['macro_type'] = 'curse'
                self.stop_macro()
                print(f"macro_type change: {self.state['macro_type']}")
                
            elif key.char == 'L':
                self.state['macro_type'] = 'poison'
                self.stop_macro()
                print(f"macro_type change: {self.state['macro_type']}")
                
            elif key.char == '}':
                self.start_kingq()
            
            elif key.char == '{':
                self.start_auto_gongj_heal()
                
        except AttributeError:
            pass

    def update_label(self):
        self.type_label.config(text=f"TYPE: {self.state['macro_type']} & {self.state['mode']}")  # Label의 텍스트 업데이트
        self.king_label.config(text=f"KING TARGET MONSTER: {self.target_monster}")  # Label의 텍스트 업데이트
        self.gongj_heal_label.config(text=f"Auto G/H : {self.state['auto_gongj_heal']}")
        self.type_label.after(100, self.update_label)  # 1000ms(1초) 후에 다시 실행
        # self.king_label.after(100, self.update_label)  # 1000ms(1초) 후에 다시 실행
                                
    def create_gui(self):
        """GUI 생성"""
        self.root = tk.Tk()
        self.root.title("바클 매크로")
        position_x, position_y = pyautogui.position()
        window_width, window_height = (400, 250)

        self.root.geometry(f"{window_width}x{window_height}+{1197}+{-340}")
        
        # Label 위젯 생성
        self.type_label = tk.Label(self.root, text="macro_type", font=("Arial", 10))
        self.type_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.gongj_heal_label = tk.Label(self.root, text="gongj_heal_mode", font=("Arial", 10))
        self.gongj_heal_label.grid(row=0, column=1, padx=10, pady=10)

        self.king_label = tk.Label(self.root, text="king_target_monster", font=("Arial", 10))
        self.king_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        
        self.start_button = tk.Button(self.root, text="매크로 시작", command=self.start_macro, width=15)
        self.start_button.grid(row=2, column=0, padx=10, pady=10)

        self.stop_button = tk.Button(self.root, text="매크로 종료", command=self.stop_macro, width=15, state=tk.DISABLED)
        self.stop_button.grid(row=2, column=1, padx=10, pady=10)
        
        self.auto_gongj_heal_button = tk.Button(self.root, text="자동 공증/힐", command=self.start_auto_gongj_heal, width=15)
        self.auto_gongj_heal_button.grid(row=3, column=0, padx=10, pady=10)
        
        self.kingq_button = tk.Button(self.root, text="왕퀘 자동 받기", command=self.start_kingq, width=15)
        self.kingq_button.grid(row=3, column=1, padx=10, pady=10)
        
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