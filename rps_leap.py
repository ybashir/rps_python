################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

import Leap, sys, thread, time
import random
import pygame
from pygame import Rect
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture, Finger
from time import sleep


class RPSListener(Leap.Listener):

    wrist_positions = [100 for i in range(360)]

    fingers = 0
    differences = []
    detection_counter = 0
    sprite_position = 150
    gesture_history = []
    
    #gestures
    ROCK = 1
    PAPER = 2 
    SCISSORS = 3
    gesture = ROCK

    #signals
    HAND_IN = 1000
    HAND_OUT = 2000
    FIST_CLOSED = 3000
    FIST_OPENED = 4000
    FIST_BUMP = 5000
    DETECTION_COMPLETE=6000

    #states
    ZERO = 100
    WAITING = 200                                                                                         
    STARTED = 300
    S1 = 400
    S2 = 500
    S3 = 600
    DETECTION = 700
    FINISHED = 800

    state = ZERO
    game_init = False
    rounds = 0
    
    state_machine = {
        ZERO: {HAND_IN:WAITING},
        WAITING: {FIST_CLOSED:STARTED},
        STARTED: {FIST_BUMP:S1, FIST_OPENED:WAITING, HAND_OUT:ZERO},
        S1: {FIST_BUMP:S2, FIST_OPENED:WAITING, HAND_OUT:ZERO},
        S2: {FIST_BUMP:S3, FIST_OPENED:WAITING, HAND_OUT:ZERO},
        S3: {FIST_BUMP:DETECTION,  HAND_OUT:ZERO},
        DETECTION: {DETECTION_COMPLETE:FINISHED},
        FINISHED: {HAND_OUT:ZERO}
    }
    def signal(self,event):       
        
        # if this event causes a transition, gets the next state, otherwise
        # stays in current state
        self.state = self.state_machine[self.state].get(event,self.state)        

        if event == self.DETECTION_COMPLETE:                
            finger_map = {
                0: self.ROCK,
                1: self.SCISSORS,
                2: self.SCISSORS,
                3: self.SCISSORS,
                4: self.PAPER,
                5: self.PAPER,
                6: self.PAPER
            }
            #computer's move
            self.gesture = finger_map[self.fingers]                                
            self.rounds = self.rounds + 1
            self.detection_counter = 0
        
        if event == self.HAND_OUT:
            self.gesture = self.ROCK
        


    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()
        if len(frame.hands) == 1:            
            # Get hands
            self.signal(self.HAND_IN)
            for hand in frame.hands:
                frames_window = 15
                position = hand.wrist_position[1]
                if self.state == self.DETECTION:
                    self.fingers += sum([f.is_extended for f in hand.fingers])                    
                    self.detection_counter += 1
                    if self.detection_counter > 5:
                        self.fingers = self.fingers/5
                        self.signal(self.DETECTION_COMPLETE)
                    return
                else:
                    self.fingers = 0
                    self.detection_counter = 0

                if hand.grab_strength > 0.9:
                    self.signal(self.FIST_CLOSED)
                else:
                    self.signal(self.FIST_OPENED)

                if self.state in [self.WAITING,self.ZERO,self.FINISHED]:
                    del(self.differences[:])
                    break
                self.sprite_position = position
                self.differences.append(position-self.wrist_positions[-1])
                if len(self.differences) > frames_window:
                    self.differences.pop(0)
                self.wrist_positions.append(position)
                self.wrist_positions.pop(0)
                
                diff = sum(self.differences)
                #print(diff)
                if diff < -125:
                    self.signal(self.FIST_BUMP)
                    del(self.differences[:])
                #print self.sprite_position
        else:
            self.signal(self.HAND_OUT)
           
        



def main():
    
    # Create a sample listener and controller
    listener = RPSListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    pygame.init()
    messages = {
            listener.WAITING : "Waiting, close fist to start",
            listener.ZERO : "Bring hand in frame",
            listener.STARTED : "Started, bump fist",
            listener.S1 : "1",
            listener.S2 : "2",
            listener.S3 : "3",
            listener.DETECTION : "Shoot",
            listener.FINISHED : "Take hand out of frame to restart"
    }

    myfont = pygame.font.SysFont('monospace', 56)

    white = 255, 255, 255
    rock = pygame.image.load("Rock.png")
    paper = pygame.image.load("Paper.png")
    scissors = pygame.image.load("Scissors.png")

    choose_image = {
        listener.ROCK: rock,
        listener.PAPER: paper,
        listener.SCISSORS: scissors
    }
    choose_text = {
        listener.ROCK: "ROCK",
        listener.PAPER: "PAPER",
        listener.SCISSORS: "SCISSORS"
    }

    size = width, height = 600, 600
    screen = pygame.display.set_mode(size)
    y = 1
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                controller.remove_listener(listener)
                sys.exit()
        screen.fill(white)

        textsurfaceA = myfont.render(messages[listener.state], 
                                    True, 
                                    (0, 100, 50))
        if listener.state == listener.FINISHED:
            textsurfaceB = myfont.render(choose_text[listener.gesture], 
                                    True, 
                                    (100, 25, 0))
            #fixme: all computer rounds result in a draw right now. this logic will change when 
            #computer takes own decisions
            textsurfaceC = myfont.render("WINS: 0 LOSSES: 0 DRAWS: %d"%listener.rounds, 
                                    True, 
                                    (100, 150, 0))
            screen.blit(textsurfaceB,(240,500))
            screen.blit(textsurfaceC,(10,550))
        
        screen.blit(choose_image[listener.gesture], 
                    Rect(150,300-listener.sprite_position,
                    300,
                    300))            
        screen.blit(textsurfaceA,(10,10))
        pygame.display.flip()
        
if __name__ == "__main__":
    main()
