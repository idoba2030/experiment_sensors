import os
from psychopy import visual, core, event, sound, prefs, gui
import csv
from pylsl import StreamInfo, StreamOutlet

# setup lsl
info = StreamInfo('MyMarkerStream', 'Markers', 1, 0, 'string', 'myuidw43536')
outlet = StreamOutlet(info)

###############################################################################
# 1) Get Subject Number via a Dialog
###############################################################################
# This dialog pops up before the experiment starts.
subject_info = {'subject_number': ''}
dlg = gui.DlgFromDict(dictionary=subject_info, title="Subject Information")
if not dlg.OK:
    core.quit()
subject_number = subject_info['subject_number']

###############################################################################
# 2) Basic Experiment Setup
###############################################################################
prefs.hardware['audioLib'] = ['sounddevice', 'pyo', 'pygame']

win = visual.Window(
    size=(1280, 720),
    fullscr=True,
    color=(0, 0, 0),
    monitor='testMonitor',
    units='pix'
)
win.mouseVisible = False

# --- Text stimuli ---
start_text = visual.TextStim(
    win,
    text='Press any key to start',
    color='white',
    height=40,
    bold=True
)
coin_text = visual.TextStim(
    win,
    text='',
    color='gold',
    pos=(0, 220),
    height=40,
    bold=True
)
warning_text = visual.TextStim(
    win,
    text='',
    color='red',
    height=40,
    bold=True,
    pos=(0, 0)
)
result_text = visual.TextStim(
    win,
    text='',
    color='yellow',
    height=40,
    pos=(0, -80),
    bold=True
)

# Black rectangle (full screen) for warnings/results
black_bg = visual.Rect(
    win,
    width=2000,
    height=2000,
    fillColor='black',
    pos=(0, 0)
)

# --- Sounds (make sure the sound files exist) ---
alarm_sound = sound.Sound('stimuli/alarm.mp3')
coin_earned_sound = sound.Sound('stimuli/coin_earned.mp3')
relief_sound = sound.Sound('stimuli/relief.mp3')
lose_all_sound = sound.Sound('stimuli/lose_all.mp3')

###############################################################################
# 3) Timing & Trial Parameters
###############################################################################
N_IMAGES = 60          # total images (or trials)
TRIAL_DURATION = 15   # seconds per image (3 for testing; 30 for real)

###############################################################################
# 4) Load Images (native resolution)
###############################################################################
def get_image_files(folder='images', valid_exts=('.jpeg', '.jpg', '.png')):
    all_files = os.listdir(folder)
    image_list = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_exts]
    image_list.sort()
    return image_list

# Load image filenames from the folder
image_files = get_image_files(folder='images', valid_exts=('.jpeg', '.jpg', '.png'))

# Create an ImageStim for each file
from psychopy import visual  # (if not already imported above)
loaded_images = []
for f in image_files:
    path = os.path.join('images', f)
    stim = visual.ImageStim(win, image=path)
    if stim.size is not None:
        stim.size = [dim * 1.5 for dim in stim.size]
    loaded_images.append(stim)

# If there are fewer than 60 images, pad with black screens; if more, take the first 60.
background_images = []
if len(loaded_images) >= N_IMAGES:
    background_images = loaded_images[:N_IMAGES]
else:
    background_images = loaded_images
    remainder = N_IMAGES - len(loaded_images)
    background_images += [black_bg for _ in range(remainder)]

###############################################################################
# 5) Define Fixed (Pre-Defined) Warning & Bonus Schedules
###############################################################################
# Warnings: define which image indices (1-based) trigger a warning (extra time after the image)
warning_images = [4, 6, 11, 13,15, 20, 24, 30, 37, 41,43, 48, 51, 56,58]#in total 15 warnings
# The second warning (i.e., the second time a warning is triggered) causes a forced loss.

# Bonuses: define which image indices yield a bonus (+1₪)
bonus_images = [2, 5,8, 10,13, 17,20,25, 28,31, 36,40, 46, 52, 59]#in total 14 bonuses

###############################################################################
# 6) Start with 5₪
###############################################################################
total_coins = 5
coin_text.text = f'Bonus: {total_coins} ₪'

###############################################################################
# 7) Show Start Screen
###############################################################################
start_text.draw()
win.flip()
outlet.push_sample(['start_screen'])  # Send start marker to LSL stream
event.clearEvents()
event.waitKeys()

coin_text.draw()
win.flip()
outlet.push_sample(['start_exp'])  # Send start marker to LSL stream

###############################################################################
# 8) Main Loop Over Images / Trials
###############################################################################
warning_count = 0  # Count of warnings encountered so far
bonus_log = []      # Log bonus events as tuples: (subject_number, image_number, coins_after_bonus)

for i in range(N_IMAGES):
    image_number = i + 1  # Image number 1..60

    # --- (A) Show the Image for TRIAL_DURATION seconds ---
    current_stim = background_images[i]
    image_end_time = core.getTime() + TRIAL_DURATION
    while core.getTime() < image_end_time:
        if 'escape' in event.getKeys():
            outlet.push_sample(['early_exit'])
            win.close()
            core.quit()

        current_stim.draw()
        coin_text.draw()
        win.flip()
        outlet.push_sample([f'image_{image_number}'])  # Send image marker to LSL stream
        core.wait(0.01)

    # --- (B) Bonus: Award bonus if this image is in bonus_images ---
    if image_number in bonus_images:
        coin_earned_sound.play()
        outlet.push_sample=(['bonus'])  # Send bonus marker to LSL stream
        total_coins += 1  # Award +1₪
        bonus_log.append((subject_number, image_number, total_coins))
        print(f"[Image {image_number}] BONUS awarded -> coins={total_coins}")

        # Show new coin total briefly on a black screen
        black_bg.draw()
        coin_text.text = f'Bonus: {total_coins} ₪'
        coin_text.draw()
        win.flip()
        core.wait(1.0)

    # --- (C) Warning: If this image triggers a warning, show the warning (extra time) ---
    if image_number in warning_images:
        warning_count += 1
        print(f"[Image {image_number}] WARNING #{warning_count} triggered.")
        alarm_sound.play()
        outlet.push_sample=(['alarm'])
        countdown_secs = 15  # Countdown duration (seconds)
        for sec in range(countdown_secs, -1, -1):
            if 'escape' in event.getKeys():
                win.close()
                core.quit()

            black_bg.draw()
            warning_text.text = (
                "WARNING! You may lose all your coins now!\n\n"
                f"Time remaining: {sec} sec"
            )
            warning_text.draw()
            win.flip()
            core.wait(1.0)
        alarm_sound.stop()

        # Forced loss on the SECOND warning encountered
        if warning_count == 2:
            print("   => FORCED LOSS: Second warning reached. Coins reset to 0.")
            total_coins = 0
            lose_all_sound.play()
            outlet.push_sample=(['lost'])
            result_text.text = "YOU LOST ALL YOUR COINS!"
        else:
            relief_sound.play()
            outlet.push_sample=(['no_lose'])
            result_text.text = "YOU SURVIVED THIS ROUND!"

        # Show result briefly on black screen
        black_bg.draw()
        coin_text.text = f'Bonus: {total_coins} ₪'
        coin_text.draw()
        result_text.draw()
        win.flip()
        core.wait(3.0)

###############################################################################
# 9) Save Bonus Log to CSV (bonus_log.csv)
###############################################################################
print("\n========== BONUS LOG ==========")
for (subj, img_num, coins) in bonus_log:
    print(f"Subject {subj} - Image {img_num} -> {coins} ₪")

with open("bonus_log.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ['subject_number', 'image_number', 'coins_after_bonus']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for (subj, img_num, coins) in bonus_log:
        writer.writerow({
            'subject_number': subj,
            'image_number': img_num,
            'coins_after_bonus': coins
        })

###############################################################################
# 10) End of Experiment
###############################################################################
outlet.push_sample=(['end'])
win.close()
core.quit()
