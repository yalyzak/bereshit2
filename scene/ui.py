import random
import time

import keyboard
from bereshit.render import Text,Box
from bereshit import World
class ui:
    def __init__(self):
        self.pause = False
        self.done = False
        self.room_found = False
        self.RoomName = None
        self.UserName = None
        self.switch = False
    def esc(self):
        if not self.pause:
            World.tick = 1/60
            for comp in list(self.parent.components.values()):
                comp.Active = True
            self.user_text.opacity = 0


            # self.box.opacity = 1

        else:
            for comp in list(self.parent.components.values()):
                if comp is not self:
                    comp.Active = False
            World.tick = 0
            self.user_text.opacity = 1
            if not self.room_found:
                self.room_text.text = "press esc and enter room passcode:"
            else:
                self.room_text.text = "enter username:"

            # self.box.opacity = 0


    def Start(self):
        self.render = self.parent.Camera.render
        self.client = self.parent.Client
        self.user_text = Text("", center=(1050,0), scale=1)
        self.box = Box(opacity=0)
        self.switch_text = Text("press shift to create a room",(0,200))
        self.render.add_text_rect(self.switch_text)
        # self.render.add_ui_rect(self.box)
        self.room_text = Text("press esc and enter room passcode:", center=(0,0), scale=1, color=(255,255,255), opacity=0.5)
        self.render.add_text_rect(self.room_text)
        self.render.add_text_rect(self.user_text)

        self.handler = keyboard.on_press(self.typing)


    def typing(self, event):
        if event.name == "esc":
            self.pause = not self.pause
            self.esc()
        if self.pause:
            if event.name == "space":
                self.user_text.text += " "
            elif event.name == "backspace":
                self.user_text.text = self.user_text.text[:-1]
            elif event.name == "enter":
                self.done = True
            elif event.name == "shift":
                self.switch = not self.switch
            elif event.name != "esc":
                self.user_text.text += event.name
    def Update(self,dt):
        if not self.switch:
            if self.done and not self.room_found:
                if self.client.FindRoom(self.user_text.text):
                    self.room_found = True
                    self.RoomName = self.user_text.text
                    self.room_text.text = "enter username: "
                    self.user_text.center = (500,0)
                else:
                    self.room_text.text = "room does not exist"
                self.user_text.text = ""
                self.done = False
        elif not self.room_found:
            self.room_found = True
            self.RoomName = self.client.CreateRoom()
            self.switch_text.text = f"your room number is {self.RoomName}"
            self.room_text.text = "enter username: "
            self.user_text.center = (500, 0)

        if self.done and self.room_found:
            if self.client.Connect(self.RoomName,self.user_text.text):
                self.UserName = self.user_text.text
                self.Active = False
                keyboard.unhook(self.handler)
                self.render.remove_text_rect(self.user_text)
                self.render.remove_text_rect(self.room_text)
                self.render.remove_text_rect(self.switch_text)
                for comp in list(self.parent.components.values()):
                    comp.Active = True
                World.tick = 1 / 60
                self.parent.Clientuse.UserName = self.UserName
                self.parent.ui2.setActive()
            else:
                self.done = False
                self.room_text.text = "username is already taken"
class ui2:
    def __init__(self):
        self.pause = False
    def esc(self):
        if not self.pause:
            World.tick = 1/60
            for comp in list(self.parent.components.values()):
                comp.Active = True


            # self.box.opacity = 1

        else:
            for comp in list(self.parent.components.values()):
                if comp is not self:
                    comp.Active = False
            World.tick = 0

    def typing(self, event):
        if event.name == "esc":
            self.pause = not self.pause
            self.esc()

    def setActive(self):
        keyboard.on_press(self.typing)









