import serial
import tkinter


def send_to_serial(serial, data: str):
    serial.write(bytes(data, "utf-8"))

arduino_serial = serial.Serial("COM7", 9600)
root = tkinter.Tk()
root.title("Soil Extraction")

frame = tkinter.Frame(root, padx=50, pady=50)
frame.pack()

drill_label = tkinter.Label(frame, text="Drilling")
drill_label.grid(row=0, column=2)
drill_button_on = tkinter.Button(frame, text="Drill On", command=lambda: send_to_serial(arduino_serial, "on"))
drill_button_off = tkinter.Button(frame, text="Drill Off", command=lambda: send_to_serial(arduino_serial, "off"))
drill_button_reverse = tkinter.Button(frame, text="Drill Reverse", command=lambda:  send_to_serial(arduino_serial, "reverse"))
drill_button_on.grid(row=1, column=1)
drill_button_off.grid(row=1, column=2)
drill_button_reverse.grid(row=1, column=3)

position_label = tkinter.Label(frame, text="Positioning")
position_label.grid(row=2, column=2)
position_button_3up = tkinter.Button(frame, text="Move Up 150mm", command=lambda: send_to_serial(arduino_serial, "3up"))
position_button_up = tkinter.Button(frame, text="Move Up 50mm", command=lambda: send_to_serial(arduino_serial, "up"))
position_button_up_fifth = tkinter.Button(frame, text="Move Up 10mm", command=lambda: send_to_serial(arduino_serial, "up5"))
position_button_3down = tkinter.Button(frame, text="Move Down 150mm", command=lambda: send_to_serial(arduino_serial, "3down"))
position_button_down = tkinter.Button(frame, text="Move Down 50mm", command=lambda: send_to_serial(arduino_serial, "down"))
position_button_down_fifth = tkinter.Button(frame, text="Move Down 10mm", command=lambda: send_to_serial(arduino_serial, "down5"))
position_button_off = tkinter.Button(frame, text="Off", command=lambda: send_to_serial(arduino_serial, "lax"))

position_button_up_fifth.grid(row=3, column=1)
position_button_down_fifth.grid(row=3, column=3)

position_button_up.grid(row=4, column=1)
position_button_down.grid(row=4, column=3)

position_button_3up.grid(row=5, column=1)
position_button_3down.grid(row=5, column=3)

position_button_off.grid(row=3, column=2)

selection_label = tkinter.Label(frame, text="Vial Selection")
selection_button1 = tkinter.Button(frame, text="Position 1", command=lambda: send_to_serial(arduino_serial, "0"))
selection_button2 = tkinter.Button(frame, text="Position 2", command=lambda: send_to_serial(arduino_serial, "1"))
selection_button3 = tkinter.Button(frame, text="Position 3", command=lambda: send_to_serial(arduino_serial, "2"))
selection_button4 = tkinter.Button(frame, text="Position 4", command=lambda: send_to_serial(arduino_serial, "3"))
selection_button5 = tkinter.Button(frame, text="Position 5", command=lambda: send_to_serial(arduino_serial, "4"))
reset_button = tkinter.Button(frame, text="Reset Position", command=lambda: send_to_serial(arduino_serial, "reset"))

selection_label.grid(row=6, column=2)
selection_button1.grid(row=7, column=0)
selection_button2.grid(row=7, column=1)
selection_button3.grid(row=7, column=2)
selection_button4.grid(row=7, column=3)
selection_button5.grid(row=7, column=4)
reset_button.grid(row=8, column=2)
  
root.mainloop()
