import pyautogui
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

def image_detection(screenshot, image_path_list, confidence=0.8, merge_thres=20, show=False, location='center'):
    screenshot_np = np.array(screenshot)  # PIL 이미지를 NumPy 배열로 변환 (BGR 형식)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # RGB → BGR 변환
    
    coordinates = []
    for image_path in image_path_list:
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        h, w = image.shape[:2]  # 높이와 너비 가져오기

        # 템플릿 매칭
        result = cv2.matchTemplate(screenshot_np, image, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= confidence)  # 매칭된 위치 추출 (신뢰도 기준)
        coordinate = list(zip(locations[1], locations[0]))
        coordinate = merge_close_coordinates(coordinate, threshold=merge_thres)
        for coordinate_ in coordinate:
            # coordinates.append(coordinate_)
            if location == 'center':
                coordinates.append((round(coordinate_[0] + w // 2), round(coordinate_[1] + h // 2)))
            elif location == 'bottom':
                coordinates.append((round(coordinate_[0] + w // 2), round(coordinate_[1] + h)))
            elif location == 'left_top':
                coordinates.append((round(coordinate_[0]), round(coordinate_[1])))
        
    if show:
        for pt in coordinates:
            cv2.rectangle(screenshot_np, pt, (pt[0] + 1, pt[1] + 1), (0, 255, 0), 5)
        cv2.imshow('Matches', screenshot_np)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    return coordinates

def extract_text_from_image(region, cut_region=(360,190,290,230), config=r'--oem 1 --psm 6'):
    if type(region) == Image.Image:
        screenshot_cut = region
    else:
        screenshot = pyautogui.screenshot(region=region, allScreens=True)
        screenshot_cut = capture_and_crop(screenshot, cut_region)
    screenshot_np = np.array(screenshot_cut)
    screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
    extracted_text = pytesseract.image_to_string(screenshot_gray, lang='kor', config=config)
    return extracted_text

def find_coordinate(coordinate_screenshot, confidence=0.7, merge_thres=5, width=75):
    coordinate = [0,0,0,0]
    for i in range(10):
        coord = image_detection(screenshot=coordinate_screenshot, image_path_list=[f'./image/num{i}.png'], confidence=confidence, merge_thres=merge_thres, show=False, location='center')
        for x,y in coord:
            if x/width <= 0.25:
                coordinate[0] = i
            elif x/width > 0.25 and x/width <= 0.50:
                coordinate[1] = i
            elif x/width > 0.50 and x/width <= 0.75:
                coordinate[2] = i
            elif x/width > 0.75 and x/width <= 1.00:
                coordinate[3] = i
    coordinate = coordinate[0]*1000 + coordinate[1]*100 + coordinate[2]*10 + coordinate[3]
    return coordinate

def get_current_coordinate(screenshot, left_cut_region = (1060,905,85,25), right_cut_region = (1150,905,85,25), confidence=0.7, merge_thres=5, width=75):
    screenshot_cut_lc = capture_and_crop(screenshot, left_cut_region)
    coord_x = find_coordinate(screenshot_cut_lc, confidence, merge_thres, width)
    screenshot_cut_rc = capture_and_crop(screenshot, right_cut_region)
    coord_y = find_coordinate(screenshot_cut_rc, confidence, merge_thres, width)
    return (coord_x, coord_y)
    