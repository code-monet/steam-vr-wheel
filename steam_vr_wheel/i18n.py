import locale
import re
import ctypes

lang_code = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
print(lang_code)
lang_code = lang_code[:2]

DEFAULT_LOCALE = 'en'
LOCALE = {}

def trim(text):
    lines = text.splitlines()
    
    # Remove leading and trailing blank (or whitespace-only) lines.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    # If no lines remain, return an empty string.
    if not lines:
        return ""
    
    # Compute the common whitespace prefix from non-empty lines.
    non_empty = [line for line in lines if line.strip()]
    common_prefix = None
    for line in non_empty:
        # Get the leading whitespace of the line.
        prefix = line[:len(line) - len(line.lstrip())]
        if common_prefix is None:
            common_prefix = prefix
        else:
            # Shorten common_prefix to the shared prefix of itself and the current line.
            new_prefix = ""
            for cp_char, p_char in zip(common_prefix, prefix):
                if cp_char == p_char:
                    new_prefix += cp_char
                else:
                    break
            common_prefix = new_prefix

    # Remove the common prefix from all lines if present.
    trimmed_lines = []
    for line in lines:
        if common_prefix == '':
            trimmed_lines.append(line.lstrip())
        elif line.startswith(common_prefix):
            trimmed_lines.append(line[len(common_prefix):])
        else:
            trimmed_lines.append(line)
    
    return "\n".join(trimmed_lines)


def replace_keys_in_text(text):
    
    def getter(key):
        l = LOCALE[key]
        c = lang_code
        if lang_code not in l:
            c = DEFAULT_LOCALE

        return l[c]

    if text in LOCALE:
        return getter(text)

    pattern = r"\{([^\}]+)\}"  # Matches any {key}

    def replacer(match):
        key = match.group(1)  # Extract key name
        if key not in LOCALE:
            return match.group[0]

        return getter(key)

    return re.sub(pattern, replacer, text)

def _I(*args):
    return " ".join(replace_keys_in_text(a) for a in args)

LOCALE = {
    'intro.main': {
        'en': """
        ---------------------

        Required vJoy version: v2.1.9.1
        Open Configure vJoy
            - Select vJoy device :   1
            - Number of buttons  :   64
            - Axes               :   all enabled
            - POVs               :   Continuous 0
            - Force Feedback     :   Enable Effects and check all

        Triple grips both hands     -     enter edit mode

        ---------------------
        """,
        'ko': """
        ---------------------

        필요한 vJoy 버전: v2.1.9.1
        Configure vJoy 실행 후 아래와 같이 설정
            - vJoy device 선택    :   1
            - Number of buttons  :   64
            - Axes               :   모두 선택
            - POVs               :   Continuous 0
            - Force Feedback     :   Enable Effects을 포함해 모두 선택

        양 손의 그립 버튼 동시에 세번 누르기     -     편집 모드

        ---------------------
        """,
        'ja': """
        ---------------------

        必要なvJoyのバージョン: v2.1.9.1
        Configure vJoyを開き、以下のように設定してください:
            - vJoy device 選択    :   1
            - Number of buttons  :   64
            - Axes               :   すべて有効
            - POVs               :   Continuous 0
            - Force Feedback     :   Enable Effectsを有効にし、すべてチェック

        両手でグリップボタンを三回同時に押すと、編集モードに入ります

        ---------------------
        """
    },
    'intro.wheel': {
        'en': """
        ----- How to use Wheel -----

        Press 'Grip' button to grab Wheel or Shifter
        While you are grabbing the Shifter's knob
            - Press A or Y        :     toggle splitter
            - Push joystick up    :     select range high
            - Push joystick down  :     select range low
            - Press 'Trigger' to unlock the reverse gear

        ----------------------------
        """,
        'ko': """
        ----- 핸들 사용법 -----
        
        '그립' 버튼을 눌러서 핸들이나 변속기를 잡을 수 있습니다
        변속기를 잡고 있을 때
            - A or Y 클릭        :     스플리터 토글
            - 조이스틱 위로 밀기    :     high 레인지 선택
            - 조이스틱 아래로 밀기  :     low 레인지 선택
            - '트리거'를 눌러서 후진 기어 락 해제

        -----------------------
        """,
        'ja': """
        ----- ハンドルの使い方 -----

        「グリップ」ボタンを押して、ハンドルまたはシフターを掴みます。
        シフターのノブを掴んでいる間に：
            - A または Y を押す     :  スプリッターの切替
            - ジョイスティックを上に押す  :  高レンジを選択
            - ジョイスティックを下に押す  :  低レンジを選択
            - 「トリガー」を押して、リバースギアのロックを解除

        ----------------------------
        """
    },
    'intro.wheel.edit_mode': {
        'en': """
        ----- EDIT MODE -----

        Touch wheel + A or X     -     set the X of wheel to 0
        Touch wheel + B or Y     -     change opacity
        Touch shifter + A or X   -     toggle sequential mode
        Touch shifter + B or Y   -     change opacity

        Grab wheel + joy left-right      -    resize
        Grab wheel + joy up-down         -    pitch
        Grab shifter + joy left-right    -    change tilt
        Grab shifter + joy up-down       -    change height

        Triple grips both hands  - exit edit mode

        ---------------------
        """,
        'ko': """
        ----- 편집 모드 -----

        핸들 터치 + A or X     -     핸들의 x좌표를 0으로 설정
        핸들 터치 + B or Y     -     투명도 변경
        변속기 터치 + A or X   -     시퀀셜 모드 토글
        변속기 터치 + B or Y   -     투명도 변경

        핸들 잡기 + 조이스틱 좌우         -    사이즈 조절
        핸들 잡기 + 조이스틱 상하         -    기울기 조절
        변속기 잡기 + 조이스틱 좌우       -    기울기 조절
        변속기 잡기 + 조이스틱 상하       -    높이 조절

        양 손의 그립 버튼 동시에 세번 누르기  -   편집 모드 나가기

        ---------------------
        """,
        'ja': """
        ----- 編集モード -----

        ハンドルに触れながら A または X を押す    - ハンドルのX座標を0に設定
        ハンドルに触れながら B または Y を押す    - 透明度を変更
        シフターに触れながら A または X を押す    - シーケンシャルモードを切替
        シフターに触れながら B または Y を押す    - 透明度を変更

        ハンドルを掴みながらジョイスティックを左右に動かす   - サイズ調整
        ハンドルを掴みながらジョイスティックを上下に動かす   - ピッチ調整
        シフターを掴みながらジョイスティックを左右に動かす  - チルト調整
        シフターを掴みながらジョイスティックを上下に動かす  - 高さ調整

        両手でグリップボタンを三回同時に押すと、編集モードを終了します

        ---------------------
        """
    },
    'intro.bike': {
        'en': "!! BIKE is WIP !!"
    },
    'cfg.selected_profile': {
        'en': "Selected Profile",
        'ko': "프로필 선택",
        'ja': "プロファイル選択"
    },
    'cfg.open_dir': {
        'en': "Open",
        'ko': "열기",
        'ja': "開く"
    },
    'cfg.save': {
        'en': "Save",
        'ko': "저장",
        'ja': "保存"
    },
    'cfg.delete': {
        'en': "Delete",
        'ko': "삭제",
        'ja': "削除"
    },
    'cfg.general': {
        'en': "General",
        'ko': "일반",
        'ja': "一般"
    },
    'cfg.trigger_pre_btn_box': {
        'en': "Button click when you rest finger on triggers",
        'ko': "트리거 위에 손가락을 얹었을 때 버튼 클릭",
        'ja': "トリガーに指を置いたときのボタンクリック"
    },
    'cfg.trigger_btn_box': {
        'en': "Button click when you press triggers",
        'ko': "트리거를 누를 때 버튼 클릭",
        'ja': "トリガーを押したときのボタンクリック"
    },
    'cfg.sfx_volume': {
        'en': "SFX Volume (%)",
        'ko': "SFX 볼륨 (%)",
        'ja': "SFXボリューム（%）"
    },
    'cfg.haptic_intensity': {
        'en': "Haptic Intensity (%)",
        'ko': "진동 세기 (%)",
        'ja': "ハプティック強度（%）"
    },
    'cfg.joystick': {
        'en': "Joystick",
        'ko': "조이스틱",
        'ja': "ジョイスティック"
    },
    'cfg.axis_deadzone': {
        'en': "Axis Deadzone (%)",
        'ko': "축 데드존 (%)",
        'ja': "軸デッドゾーン（%）"
    },
    'cfg.pnl_joystick_frame': {
        'en': "Axis or Button",
        'ko': "축 또는 버튼",
        'ja': "軸またはボタン"
    },
    'cfg.pnl_joystick_frame_descr': {
        'en': "Checked joystick direction will act as button",
        'ko': "선택된 조이스틱 방향은 버튼이 됩니다",
        'ja': "選択されたジョイスティックの方向はボタンとして機能します"
    },
    'cfg.multibutton_trackpad_box': {
        'en': "Joystick has 4 additional click regions",
        'ko': "조이스틱에 4개의 추가 클릭 영역을 할당",
        'ja': "ジョイスティックに4つのクリック領域を追加する"
    },
    'cfg.multibutton_trackpad_box_descr': {
        'en': """Joysticks (or trackpads on VIVE) have 4 more buttons registered
                 Center, left, right, down, and up totaling 5 click regions""",
        'ko': """조이스틱(또는 VIVE의 트랙패드)에 4개의 추가 버튼 할당
                 중앙, 왼쪽, 오른쪽, 아래, 위 총 5개의 클릭 영역을 할당""",
        'ja': """ジョイスティック（またはVIVEのトラックパッド）に、4つの追加ボタンを登録
                 中央、左、右、下、上の合計5つのクリック領域があります"""
    },
    'cfg.wheel': {
        'en': "Wheel",
        'ko': "핸들",
        'ja': "ハンドル"
    },
    'cfg.wheel_degrees': {
        'en': "Wheel Rotation (Degrees)",
        'ko': "핸들 회전 반경 (도)",
        'ja': "ハンドル回転（度）"
    },
    'cfg.wheel_degrees_descr': {
        'en': "360=F1 540-1080=Rally car 1440=Default 900-1800=Truck",
        'ko': "360=F1 540-1080=랠리카 1440=기본 900-1800=트럭",
        'ja': "360=F1 540-1080=ラリーカー 1440=デフォルト 900-1800=トラック"
    },
    'cfg.wheel_pitch': {
        'en': "Wheel Tilt (Degrees)",
        'ko': "핸들 기울기 (도)",
        'ja': "ハンドル傾斜（度）"
    },
    'cfg.wheel_alpha': {
        'en': "Wheel Opacity (%)",
        'ko': "핸들 불투명도 (%)",
        'ja': "ハンドル不透明度（%）"
    },
    'cfg.wheel_transparent_center_box': {
        'en': "Wheel becomes transparent while looking at it",
        'ko': "핸들을 바라볼 때 핸들이 투명해집니다.",
        'ja': "ハンドルを見ているときに透明になる"
    },
    'cfg.wheel_centering': {
        'en': "Wheel Centering",
        'ko': "핸들 센터링",
        'ja': "ハンドルセンタリング"
    },
    'cfg.wheel_centerforce': {
        'en': "Center Force (%)",
        'ko': "센터링 강도 (%)",
        'ja': "センタリング力（%）"
    },
    'cfg.wheel_ffb': {
        'en': "Use Force Feedback to center the wheel",
        'ko': "핸들 센터링에 포스 피드백 사용",
        'ja': "ハンドルセンタリングにフォースフィードバックを使用する"
    },
    'cfg.wheel_ffb_haptic': {
        'en': "Force Feedback haptic on bumpy roads",
        'ko': "고르지 않은 도로에서 포스 피드백 진동",
        'ja': "凹凸のある道でのフォースフィードバックハプティック"
    },
    'cfg.wheel_grab_behavior': {
        'en': "Grab Behavior",
        'ko': "잡기 방식",
        'ja': "掴み方式"
    },
    'cfg.wheel_grabbed_by_grip_box': {
        'en': "Manual wheel grabbing",
        'ko': "수동 핸들 잡기",
        'ja': "手動でハンドルを掴む"
    },
    'cfg.wheel_grabbed_by_grip_box_toggle': {
        'en': "Grabbing object is NOT toggle",
        'ko': "물체 잡기는 토글이 아님",
        'ja': "掴む操作はトグルではない"
    },
    'cfg.shifter': {
        'en': "H Shifter",
        'ko': "변속기",
        'ja': "Hシフター"
    },
    'cfg.shifter_degree': {
        'en': "Shifter Tilt (Degrees)",
        'ko': "변속기 기울기 (도)",
        'ja': "シフター傾斜（度）"
    },
    'cfg.shifter_alpha': {
        'en': "Shifter Opacity (%)",
        'ko': "변속기 불투명도 (%)",
        'ja': "シフター不透明度（%）"
    },
    'cfg.shifter_scale': {
        'en': "Shifter Height Scale (%)",
        'ko': "변속기 높이 (%)",
        'ja': "シフター高さ（%）"
    },
    'cfg.shifter_scale_descr': {
        'en': "Height Scale 100%=Truck Height Scale 30%=General",
        'ko': "높이 100%=트럭 높이 30%=일반",
        'ja': "高さ 100%＝トラック 30%＝一般"
    },
    'cfg.shifter_sequential': {
        'en': "Sequential Mode",
        'ko': "시퀀셜 변속기 모드",
        'ja': "シーケンシャルモード"
    },
    'cfg.shifter_rev': {
        'en': "Reverse Gear Position",
        'ko': "후진 기어 위치",
        'ja': "リバースギアの位置"
    },
    'cfg.shifter_rev_tl': {
        'en': "Top Left",
        'ko': "왼쪽 상단",
        'ja': "左上"
    },
    'cfg.shifter_rev_tr': {
        'en': "Top Right",
        'ko': "오른쪽 상단",
        'ja': "右上"
    },
    'cfg.shifter_rev_bl': {
        'en': "Bottom Left",
        'ko': "왼쪽 하단",
        'ja': "左下"
    },
    'cfg.shifter_rev_br': {
        'en': "Bottom Right",
        'ko': "오른쪽 하단",
        'ja': "右下"
    },
    'cfg.bike': {
        'en': "Bike",
        'ko': "바이크",
        'ja': "バイク"
    },
    'cfg.bike_show_handlebar': {
        'en': "Show Handlebar Overlay",
        'ko': "핸들바 오버레이 표시",
        'ja': "ハンドルバーオーバーレイ表示"
    },
    'cfg.bike_show_hands': {
        'en': "Show Hands Overlay",
        'ko': "손 오버레이 표시",
        'ja': "ハンズオーバーレイ表示"
    },
    'cfg.bike_use_ac_server': {
        'en': "Use Assetto Corsa telemetry to calibrate max lean",
        'ko': "최대 기울기 보정을 위해 Assetto Corsa 텔레메트리 사용",
        'ja': "Assetto Corsaのテレメトリを使用して最大傾斜を校正する"
    },
    'cfg.bike_max_lean': {
        'en': "Lean Angle (Degrees)",
        'ko': "기울기 각도 (도)",
        'ja': "傾斜角（度）"
    },
    'cfg.bike_max_steer': {
        'en': "Max Steer (Degrees)",
        'ko': "최대 조향 (도)",
        'ja': "最大操舵角（度）"
    },
    'cfg.bike_throttle_sensitivity': {
        'en': "Throttle Sensitivity (%)",
        'ko': "스로틀 민감도 (%)",
        'ja': "スロットル感度（%）"
    },
    'cfg.bike_throttle_decrease_per_sec': {
        'en': "Throttle Decrease per Second (%)",
        'ko': "초당 스로틀 감소 (%)",
        'ja': "スロットル減少率（%/秒）"
    },
    'cfg.bike_mode_absolute_radio': {
        'en': "Use Absolute Positioning",
        'ko': "절대 위치 지정 사용",
        'ja': "絶対位置指定を使用する"
    },
    'cfg.bike_mode_relative_radio': {
        'en': "Use Relative Positioning",
        'ko': "상대 위치 지정 사용",
        'ja': "相対位置指定を使用する"
    },
    'cfg.bike_mode_absolute_radio_descr': {
        'en': "Position of hands determines the lean angle",
        'ko': "손의 위치가 기울기 각도를 결정합니다.",
        'ja': "手の位置が傾斜角を決定します"
    },
    'cfg.bike_absolute_box': {
        'en': "Absolute Mode",
        'ko': "절대 위치 모드",
        'ja': "絶対モード"
    },
    'cfg.bike_handlebar_height': {
        'en': "Handlebar Height (cm)",
        'ko': "핸들바 높이 (cm)",
        'ja': "ハンドルバーの高さ（cm）"
    },
    'cfg.bike_handlebar_height_descr': {
        'en': "In-game bike model handlebar's height from the floor",
        'ko': "게임 내 바이크크 모델 핸들바의 바닥으로부터의 높이",
        'ja': "ゲーム内バイクモデルのハンドルバーの床からの高さ"
    },
    'cfg.bike_mode_relative_radio_descr': {
        'en': "Angle between two hands determine the lean angle",
        'ko': "두 손 사이의 각도가 기울기 각도를 결정합니다.",
        'ja': "両手の角度が傾斜角を決定します"
    },
    'cfg.bike_relative_box': {
        'en': "Relative Mode",
        'ko': "상대 위치 모드",
        'ja': "相対モード"
    },
    'cfg.bike_relative_sensitivity': {
        'en': "Sensitivity (%)",
        'ko': "민감도 (%)",
        'ja': "感度（%）"
    },
    'cfg.advanced_mode': {
        'en': "Advanced Mode",
        'ko': "고급 모드",
        'ja': "詳細設定モード"
    },
    'cfg.advanced': {
        'en': "Advanced",
        'ko': "고급",
        'ja': "詳細設定"
    },
    'cfg.advanced_descr': {
        'en': "Consult the source code for its usage"
    }
}

for key, val in LOCALE.items():
    for l, txt in val.items():
        val[l] = trim(txt)
        #print(val[l])