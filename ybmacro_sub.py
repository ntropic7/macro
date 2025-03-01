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
		self.game_region = (223, 51, 1665, 956)
		self.hpmp_region = (1679, 859, 183, 44)

		self.state = {'macro_running': False, 'macro_type':'auto_hunt', 'mode': 'normal', 'auto_gongj_heal':'OFF', 'macro_pause':False}
		self.skill_mapping = {
			'mabi' : {'skk':'1', 'delay':0.02, 'direction':keyboard.Key.left},
			'curse' : {'skk':'2', 'delay':0.02, 'direction':keyboard.Key.left},
			'heal': {'skk':'3', 'delay':0.02, 'direction':keyboard.Key.home},
			'attack': {'skk':'4', 'delay':0.2, 'direction':keyboard.Key.left},
			'gongj': {'skk':'5', 'delay':0.05, 'direction':None},
			'attack_chum': {'skk':'6', 'delay':0.04, 'direction':None},
			'attack_chum2': {'skk':'7', 'delay':0.04, 'direction':None},
			'poison': {'skk':'8', 'delay':0.02, 'direction':keyboard.Key.left},
			'despair': {'skk':'9', 'delay':0.02, 'direction':keyboard.Key.left},
			'hellfire': {'skk':'0', 'delay':0.5, 'direction':keyboard.Key.left},
			'boho': {'skk':'x', 'delay':0.1, 'direction':keyboard.Key.home},
			'muzang': {'skk':'z', 'delay':0.1, 'direction':keyboard.Key.home},

		}
		self.mouse_controller = mouse.Controller()
		self.keyboard_controller = keyboard.Controller()

		self.mp_thres = 0.6
		self.hp_thres = 0.6
		self.skill_done = 1
		self.bomu_time = time.time() - 999
		self.mabi_time = time.time() - 999

		# GUI 요소 초기화
		self.root = None
		self.start_button = None
		self.stop_button = None
		self.auto_gongj_heal_button = None

	def _active_skill(self, skill_name, target_iter=1, reset_tap=False):
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
		delay = random.uniform(0.005, 0.005 + 0.001)
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
		screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
		mp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(self.mp_thres-0.1, self.mp_thres, 0.005)])
		mp_color_low = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.005)])
		while mp_color < 30:
			self.state['macro_pause'] = True
			if run and self.state['auto_gongj_heal']!='ON':
				self.state['macro_pause'] = False
				raise
			if self.skill_done == 1:
				if mp_color_low < 40:
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
				mp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(self.mp_thres-0.1, self.mp_thres, 0.01)])
				mp_color_low = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]*3/4))) for x in np.arange(0.1, 0.2, 0.01)])
		self.state['macro_pause'] = False

	def auto_heal(self, run=False):
		screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
		hp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]/4))) for x in np.arange(self.hp_thres-0.1, self.hp_thres, 0.005)])
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
				screenshot = pyautogui.screenshot(region=self.hpmp_region, allScreens=True)
				hp_color = np.mean([screenshot.getpixel((round((1-x) * self.hpmp_region[2]),round(self.hpmp_region[3]/4))) for x in np.arange(self.hp_thres-0.1, self.hp_thres, 0.005)])
		self.state['macro_pause'] = False

	def auto_bomu(self):
		if time.time() - self.bomu_time > 60:
			self.state['macro_pause'] = True
			if self.skill_done == 1:
				time.sleep(0.02)
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
				dirs = ['left', 'up', 'down', 'right']
				for active_i in dirs:
					if not self.state['macro_running']:
						self._reset_tap()
						raise
					self._active_skill(skill_name='mabi', target_iter=1, reset_tap=True)
					self._change_direction(tap_method='natural')
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
				self.skill_mapping['mabi']['delay']=0.005
				macro_type = 'mabi'
				self.active_spell_auto(skill_name=['mabi', 'poison'], macro_type=macro_type, target_iter=[1,1], active_iter=20, change_dir=True, auto_bomu=True, auto_mabi=False)

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
			time.sleep(0.05)
			
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
			if key.char in ['A']:
				if self.state['macro_running']:
					self.stop_macro()
				else:
					self.start_macro()

		except AttributeError:
			pass

	def on_release(self, key):
		"""키 해제 감지"""
		try:  
			if key.char == '>':
				self._active_skill(skill_name='boho', target_iter=1)
				self._active_skill(skill_name='muzang', target_iter=1)

			elif key.char == 'S':
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

			elif key.char == 'P':
				self.state['macro_type'] = 'poison'
				self.stop_macro()
				print(f"macro_type change: {self.state['macro_type']}")

			elif key.char == '{':
				self.start_auto_gongj_heal()

		except AttributeError:
			pass

	def update_label(self):
		self.type_label.config(text=f"TYPE: {self.state['macro_type']} & {self.state['mode']}")  # Label의 텍스트 업데이트
		self.gongj_heal_label.config(text=f"Auto G/H : {self.state['auto_gongj_heal']}")
		self.type_label.after(100, self.update_label)  # 1000ms(1초) 후에 다시 실행

	def create_gui(self):
		"""GUI 생성"""
		self.root = tk.Tk()
		self.root.title("옛바 매크로")
		position_x, position_y = pyautogui.position()
		window_width, window_height = (550, 180)

		self.root.geometry(f"{window_width}x{window_height}+{20}+{60}")

		# Label 위젯 생성
		self.type_label = tk.Label(self.root, text="macro_type", font=("Arial", 10))
		self.type_label.grid(row=0, column=0, padx=10, pady=10)

		self.gongj_heal_label = tk.Label(self.root, text="gongj_heal_mode", font=("Arial", 10))
		self.gongj_heal_label.grid(row=0, column=1, padx=10, pady=10)

		self.start_button = tk.Button(self.root, text="매크로 시작", command=self.start_macro, width=15)
		self.start_button.grid(row=1, column=0, padx=10, pady=10)

		self.stop_button = tk.Button(self.root, text="매크로 종료", command=self.stop_macro, width=15, state=tk.DISABLED)
		self.stop_button.grid(row=1, column=1, padx=10, pady=10)

		self.auto_gongj_heal_button = tk.Button(self.root, text="자동 공증/힐", command=self.start_auto_gongj_heal, width=15)
		self.auto_gongj_heal_button.grid(row=2, column=0, padx=10, pady=10)

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