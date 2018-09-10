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
        
    def signal(self,event):
        
        if event == self.HAND_IN:
            if self.state == self.ZERO:
                self.state = self.WAITING
        
        elif event == self.FIST_CLOSED:
            if self.state == self.WAITING:
                self.state = self.STARTED
        
        elif event == self.FIST_OPENED:
            if self.state in [self.STARTED,self.S1,self.S2]:
                self.state = self.WAITING

        elif event == self.FIST_BUMP:
            if self.state == self.STARTED:
                self.fingers = 0
                self.state = self.S1
            elif self.state == self.S1:
                self.state = self.S2
            elif self.state == self.S2:
                self.state = self.S3
            elif self.state == self.S3:
                self.state=self.DETECTION
                
        elif event == self.DETECTION_COMPLETE:
            if self.state == self.DETECTION:
                print self.fingers
                if self.fingers == 0:
                    self.gesture = self.ROCK
                elif self.fingers >= 1 and self.fingers <= 3:
                    self.gesture = self.SCISSORS
                elif self.fingers > 3:
                    self.gesture = self.PAPER
                self.state = self.FINISHED
                self.rounds = self.rounds + 1
            self.detection_counter = 0
        elif event == self.HAND_OUT:
            if self.state != self.ZERO:
                self.state = self.ZERO
                self.gesture = self.ROCK



    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()
        if len(frame.hands) == 1:            
            # Get hands
            self.signal(self.HAND_IN)
            for hand in frame.hands:
                frames_window = 30
                position = hand.wrist_position[0]+150
                if self.state == self.DETECTION:
                    self.fingers += sum([1 if finger.is_extended else 0 for finger in hand.fingers])
                    self.gesture_history.append([1 if finger.is_extended else 0 for finger in hand.fingers])
                    self.detection_counter += 1
                    if self.detection_counter > 5:
                        self.fingers = self.fingers/5
                        self.signal(self.DETECTION_COMPLETE)
                        #print self.gesture_history
                        del self.gesture_history[:]
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
                if diff > 125:
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

    myfont = pygame.font.SysFont('monospace', 40)
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
            if event.type == pygame.QUIT: sys.exit()
        screen.fill(white)

        textsurfaceA = myfont.render(messages[listener.state], 
                                    True, 
                                    (0, 100, 50))
        if listener.state == listener.FINISHED:
            textsurfaceB = myfont.render(choose_text[listener.gesture], 
                                    True, 
                                    (100, 25, 0))
            textsurfaceC = myfont.render("WINS: 0 LOSSES: 0 DRAWS: %d"%listener.rounds, 
                                    True, 
                                    (100, 150, 0))
            screen.blit(textsurfaceB,(240,500))
            screen.blit(textsurfaceC,(100,550))
        
        screen.blit(choose_image[listener.gesture], 
                    Rect(150,listener.sprite_position,
                    300,
                    300))            
        screen.blit(textsurfaceA,(10,10))
        pygame.display.flip()
        
        


    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        # Remove the sample listener when done
        controller.remove_listener(listener)
    
    
if __name__ == "__main__":
    main()
