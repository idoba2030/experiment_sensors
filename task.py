from psychopy import visual, core, event, sound, prefs
from pylsl import StreamInfo, StreamOutlet

# setup lsl
info = StreamInfo('MyMarkerStream', 'Markers', 1, 0, 'string', 'myuidw43536')
outlet = StreamOutlet(info)

# Set preferred audio engine
prefs.hardware['audioLib'] = ['sounddevice', 'pyo', 'pygame']

# Initialize window and hide cursor
win = visual.Window(size=(1280, 720), fullscr=True, color=(0, 0, 0), monitor='testMonitor', units='norm')
win.mouseVisible = False  # Hide mouse cursor

# Initialize text components
start_text = visual.TextStim(win, text='Press any key to start', color='white', height=0.15, bold=True)
coin_text = visual.TextStim(win, text='', color='gold', height=0.15, pos=(0, 0.5), bold=True)
warning_text = visual.TextStim(win, text='', color='red', height=0.15, pos=(0, 0), bold=True)
countdown_text = visual.TextStim(win, text='', color='white', height=0.12, pos=(0, -0.3), bold=True)
result_text = visual.TextStim(win, text='', color='yellow', height=0.15, pos=(0, -0.5), bold=True)

# Visual elements for earnings
coin_bar = visual.Rect(win, width=0.4, height=0.05, fillColor='gold', pos=(0, 0.2))
background = visual.Rect(win, width=1.8, height=1.8, fillColor='black')

# Initialize sounds
alarm_sound = sound.Sound('stimuli/alarm.mp3')
coin_earned_sound = sound.Sound('stimuli/coin_earned.mp3')
relief_sound = sound.Sound('stimuli/relief.mp3')
lose_all_sound = sound.Sound('stimuli/lose_all.mp3')

# Experiment parameters
total_coins = 5.0  # Start at 5.00 Shekels
exp_duration = 1800  # Total experiment duration (30 minutes)
timer = core.Clock()  # Use precise timer

# Define event schedule (only **one** loss at 180 sec)
event_schedule = {
    30: {"type": "increase", "amount": 0.1},
    60: {"type": "increase", "amount": 0.1},
    90: {"type": "warning", "loss": False},
    120: {"type": "increase", "amount": 0.1},
    150: {"type": "increase", "amount": 0.1},
    180: {"type": "warning", "loss": True},  # **Only loss event at 180 sec**
    210: {"type": "increase", "amount": 0.1},
    240: {"type": "increase", "amount": 0.1},
    270: {"type": "warning", "loss": False},
}

# **Continue the pattern until 1800 sec**
for t in range(300, exp_duration + 1, 30):
    if t % 90 == 0:
        event_schedule[t] = {"type": "warning", "loss": False}
    else:
        event_schedule[t] = {"type": "increase", "amount": 0.1}

# Show start screen
start_text.draw()
win.flip()
outlet.push_sample(['start_screen'])
event.clearEvents()
event.waitKeys()  # Wait for key press

# Show initial 5.00 Shekels
coin_text.text = 'Bonus: 5.00 Shekels'
background.draw()
coin_text.draw()
coin_bar.draw()
win.flip()
outlet.push_sample(['start_show_bonus'])

# Start timer
start_time = timer.getTime()

# Run experiment
for time_point in sorted(event_schedule.keys()):
    # Wait until the event time
    while timer.getTime() - start_time < time_point:
        if 'escape' in event.getKeys():
            outlet.push_sample(['early_exit'])
            win.close()
            core.quit()
        core.wait(0.01)  # Reduce delay for better responsiveness

    event_type = event_schedule[time_point]["type"]

    if event_type == "increase":
        # **Play sound slightly BEFORE screen update**
        coin_earned_sound.play()
        core.wait(0.2)  # Small delay for natural response

        # Increase Bonus
        total_coins += event_schedule[time_point]["amount"]
        coin_text.text = f'Bonus: {total_coins:.2f} Shekels'
        coin_bar.width = max(0.4 + (total_coins * 0.005), 0.1)

        # Draw updated elements
        background.draw()
        coin_text.draw()
        coin_bar.draw()
        win.flip()
        outlet.push_sample([f'coin_increase_{time_point}'])

        core.wait(0.8)  # Remaining time after initial 0.2s

    elif event_type == "warning":
        print(f"WARNING triggered at {time_point} seconds")  # Debugging

        alarm_sound.play()
        for i in range(10, -1, -1):  # **Keep the warning on the screen longer**
            warning_text.text = 'WARNING! You may lose all your coins now!'
            countdown_text.text = f'Time remaining: {i} sec'

            # Draw elements
            background.draw()
            warning_text.draw()
            countdown_text.draw()
            win.flip()
            outlet.push_sample([f'warning_{time_point}_countdown_{i}'])
            core.wait(1)

        alarm_sound.stop()

        # **Only reset coins at 180 sec**
        if event_schedule[time_point]["loss"]:
            print("Losing all coins at 180 sec!")  # Debugging
            total_coins = 0.0
            result_text.text = 'YOU LOST ALL YOUR COINS!'
            lose_all_sound.play()
            coin_bar.width = 0.4  # Reset bar
            result_label = 'loss'
        else:
            result_text.text = 'YOU SURVIVED THIS ROUND!'
            relief_sound.play()
            result_label = 'survived'

        # Draw result
        background.draw()
        result_text.draw()
        win.flip()
        outlet.push_sample([f'result_{time_point}_{result_label}'])
        core.wait(10)  # **Increase display time from 3 sec to 10 sec**

# End of experiment
outlet.push_sample(['experiment_end'])
win.close()
core.quit()
