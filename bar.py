import time
import sys
import RPi.GPIO as GPIO
#from RPi import GPIO
import json
from threading import Thread
import traceback
import pickle


class Bar:

    class Drink:

        class Version:

            def __init__(self, shortname: str, ingredients: [object], proportions: [float], glassize: int) -> object:
                self.shortname = shortname
                self.glassize = glassize

                assert (len(ingredients) == len(proportions)), "No. of drinks and no. of proportions must be equal."

                self.ingredients = ingredients  # list of Ingredient-Instances
                self.proportions = proportions  # list of distribution

                # for ingredient in ingredients:
                #    ingredient.assignTo(self)

            @classmethod
            def by_mililiters(cls, shortname, ingredients, volumina):
                # self.shortname = shortname
                assert (len(ingredients) == len(volumina)), "No. of drinks and no. of proportions must be equal."
                glassize = 0
                for volume in volumina:
                    glassize += volume
                proportions = []
                for volume in volumina:
                    proportions.append(volume / glassize * 100)
                return cls(shortname, ingredients, proportions, glassize)

            @property
            def available(self):
                for ingredient, proportion in zip(self.ingredients, self.proportions):
                    need = proportion / 100 * self.glassize
                    if not ingredient.available(need):
                        return False
                return True

            #    def make(self): (deprecated)
            #        # To Do
            #        threads = []
            #        needs = []
            #        for ingredient, proportion in zip(self.ingredients, self.proportions):
            #            need = proportion / 100 * self.glassize
            #            t = Thread(target=ingredient.pump.pour, args=(need,))
            #            t.start()
            #            threads.append(t)
            #            needs.append(need)
            #        while threads:
            #            for thread, ingredient, need in zip(threads, self.ingredients, needs):
            #                if thread.is_alive():
            #                    continue
            #                threads.remove(thread)
            #                ingredient.use(need)

            def make(self):
                # To Do
                threads = []
                for ingredient, proportion in zip(self.ingredients, self.proportions):
                    need = proportion / 100 * self.glassize
                    t = Thread(target=ingredient.pump.pour, args=(need,))
                    t.start()
                    threads.append(t)
                    ingredient.use(need)

            @property
            def duration(self):
                duration = 0
                for ingredient, proportion in zip(self.ingredients, self.proportions):
                    need = proportion / 100 * self.glassize
                    duration = max(duration, ingredient.pump.duration(volume=need))
                return duration

            def change_ingredients(self, ingredients: [object], proportions: [float]):

                assert (len(ingredients) == len(proportions)), "No. of drinks and no. of proportions must be equal."

                self.ingredients = ingredients  # list of Ingredient-Instances
                self.proportions = proportions  # list of distribution

        def __init__(self, name: str, type: str, picture: str, description: str) -> object:
            self.name = name
            self.type = type
            self.picture = picture  # name of picture file
            self.description = description
            self.versions = []

        def create_version(self, shortname: str, ingredients: [object], proportions: [float], glassize: int):
            version = self.Version(shortname, ingredients, proportions, glassize)
            self.versions.append(version)

        def delete_version(self, versionid):
            del self.versions[versionid]

        @property
        def available(self):
            for version in self.versions:
                if version.available:
                    return True
                return False

    class Ingredient:

        # available = false # => muss in Methode

        def __init__(self, name: str, percentage: float, bottlesize: float, remaining: float = None) -> object:
            self.name = name
            self.percentage = percentage  # in 0 - 100
            self.bottlesize = bottlesize  # in ml
            if remaining is None:
                self.remaining = bottlesize
            else:
                self.remaining = remaining  # in ml
            self.assignedTo = []

        def assignPump(self, pump: object):
            self.pump = pump

        def unplug(self):
            self.pump = None

        def available(self, need=0):
            if self.pump is None:
                return False
            if self.remaining - need < 0:
                return False
            return True

        def use(self, amount):
            self.remaining = self.remaining - amount

        def swapBottle(self):
            self.remaining = self.bottlesize

        def assignTo(self, version: object):
            self.assignedTo.append(version)

        def deleteFrom(self, version: object):
            self.assignedTo.remove(version)

        def change_Ingredient(self, name: str, percentage: float, bottlesize: float, pump: object = None, remaining: float = None):
            self.name = name
            self.percentage = percentage
            self.bottlesize = bottlesize
            if remaining is None:
                self.remaining = bottlesize
            else:
                self.remaining = remaining  # in ml
            if pump is None:
                self.unplug()
            else:
                self.assignPump(pump)

    # follow_up: method for new bottle, state of bottle, auto availability



    class Pump:

        def __init__(self, pin: int, flowrate: int = 500) -> object:
            #self.number = number
            self.pin = pin
            self.flowrate = flowrate  # standard: 500 ml/min

        def pour(self, volume):
            duration = volume / self.flowrate * 60
            GPIO.output(self.pin, GPIO.LOW)
            print('Start pouring from pin {} ...'.format(self.pin))
            time.sleep(duration)
            
            GPIO.output(self.pin, GPIO.HIGH)
            print('Stop pouring from pin {}, time elapsed: {}s.'.format(self.pin, duration))

        def duration(self, volume):
            return volume / self.flowrate * 60

        def clean(self):
            GPIO.output(self.pin, GPIO.LOW)
            print('Start cleaning pin {} ...'.format(self.pin))
            time.sleep(10)
            GPIO.output(self.pin, GPIO.HIGH)
            print('Stop cleaning pin {} ...'.format(self.pin))

    def __init__(self):
        # check if saved drinks, ingredients, pumps, versions
        # otherwise create empty objects
        self.drinks = []
        self.ingredients = []
        self.pumps = []

    def create_drink(self, name: str, type: str, picture: str, description: str):
        drink = self.Drink(name, type, picture, description)
        self.drinks.append(drink)

    def delete_drink(self, drink):
        self.drinks.remove(drink)

    def create_ingredient(self, name: str, percentage: float, bottlesize: float, remaining: float = None, pump: int = None):
        ingredient = self.Ingredient(name, percentage, bottlesize, remaining)
        if pump:
            ingredient.assignPump(self.pumps[pump])
        self.ingredients.append(ingredient)

    def pos_delete_ingredient(self, ingredient):
        for drink in self.drinks:
            for version in drink.versions:
                for assignedIng in version.ingredients:
                    if ingredient == assignedIng:
                        return False
        return True

    def delete_ingredient(self, ingredient):
        for drink in self.drinks:
            for version in drink.versions:
                for assignedIng in version.ingredients:
                    if ingredient == assignedIng:
                        return "assigned"
        self.ingredients.remove(ingredient)
        return 0

    def create_pump(self, pin: int, flowrate: int = 500):
        pump = self.Pump(pin, flowrate)
        self.pumps.append(pump)

    def pos_delete_pump(self, pump):
        for ingredient in self.ingredients:
            if ingredient.pump == pump:
                return False
        return True

    def delete_pump(self, pump: object):
        if not self.pos_delete_ingredient(pump):
            return "assigned"
        self.pumps.remove(pump)
        return 0

    def save_config(self, folder):
        with open(folder + '/config.obj', 'wb') as filehandler:
            pickle.dump(self, filehandler)
        '''
        filehandler = open(folder + '/drinks.obj', 'wb')
        pickle.dump(self.drinks, filehandler)
        filehandler = open(folder + '/ingredients.obj', 'wb')
        pickle.dump(self.ingredients, filehandler)
        filehandler = open(folder + '/pumps.obj', 'wb')
        pickle.dump(self.pumps, filehandler)
        '''

    def reload_config(self, folder):
        pass
        '''
        filehandler = open(folder + '/drinks.obj', 'rb')
        self.drinks = pickle.load(filehandler)
        filehandler = open(folder + '/ingredients.obj', 'rb')
        self.ingredients = pickle.load(filehandler)
        filehandler = open(folder + '/pumps.obj', 'rb')
        self.pumps = pickle.load(filehandler)
        '''

    def __del__(self):
        self.save_config('config')

def reload_config(folder):
    with open(folder + '/config.obj', 'rb') as filehandler:
        return pickle.load(filehandler)
