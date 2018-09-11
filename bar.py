import time
import sys
#import RPi.GPIO as GPIO
from RPi import GPIO
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

    def __init__(self, folder:str = None):
        # check if saved drinks, ingredients, pumps, versions
        # otherwise create empty objects
        self.drinks = []
        self.ingredients = []
        self.pumps = []
        if folder:
            print("Reloading config from json..")
            self.reload_config(folder)

    def create_drink(self, name: str, type: str, picture: str, description: str):
        drink = self.Drink(name, type, picture, description)
        self.drinks.append(drink)

    def delete_drink(self, drink):
        self.drinks.remove(drink)

    def create_ingredient(self, name: str, percentage: float, bottlesize: float, remaining: float = None, pump: int = None):
        ingredient = self.Ingredient(name, percentage, bottlesize, remaining)
        if pump != None:
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

        json_pumps = []
        json_ingredients = []
        json_drinks=[]

        for pump in self.pumps:
            json_pumps.append({
                "pin": pump.pin,
                "flowrate": pump.flowrate
            })
        for ing in self.ingredients:
            dic = {
                "name": ing.name,
                "percentage": ing.percentage,
                "bottlesize": ing.bottlesize,
                "remaining": ing.remaining,
                "pump": self.pumps.index(ing.pump)
            }
            json_ingredients.append(dic)
        for drink in self.drinks:
            dic = {
                "name": drink.name,
                "type": drink.type,
                "picture": drink.picture,
                "description": drink.description
            }
            versions = []
            for version in drink.versions:
                vdic = {
                    "shortname": version.shortname,
                    "glassize": version.glassize,
                    "proportions": version.proportions
                }
                ingredients = []
                for ing in version.ingredients:
                    ingredients.append(self.ingredients.index(ing))
                vdic["ingredients"] = ingredients
                versions.append(vdic)
            dic["versions"] = versions
            json_drinks.append(dic)
        with open(folder + "/pumps.json", "w") as write_file:
            json.dump(json_pumps, write_file, indent=4, sort_keys=True)
        with open(folder + "/ingredients.json", "w") as write_file:
            json.dump(json_ingredients, write_file, indent=4, sort_keys=True)
        with open(folder + "/drinks.json", "w") as write_file:
            json.dump(json_drinks, write_file, indent=4, sort_keys=True)


    def reload_config(self, folder):
        try:
            pumps = []
            ingredients = []
            drinks = []

            with open(folder + "/pumps.json", "r") as read_file:
                pumps = json.load(read_file)
            print(pumps)
            with open(folder + "/ingredients.json", "r") as read_file:
                ingredients = json.load(read_file)
            print(ingredients)
            with open(folder + "/drinks.json", "r") as read_file:
                drinks = json.load(read_file)
            print(drinks)
            print("Reloading pumps..")
            for pump in pumps:
                self.create_pump(pin=pump["pin"], flowrate=pump["flowrate"])
            print("Reloading bottles..")
            for ing in ingredients:
                self.create_ingredient(name=ing["name"], percentage=ing["percentage"], bottlesize=ing["bottlesize"],
                                       remaining=ing["remaining"], pump=ing["pump"])
            print("Reloading drinks..")
            for iddrink, drink in enumerate(drinks):
                self.create_drink(name=drink["name"], type=drink["type"],
                                  picture=drink["picture"], description=drink["description"])
                versions = drink["versions"]
                for version in versions:
                    version_ings = []
                    for ingid in version["ingredients"]:
                        version_ings.append(self.ingredients[ingid])
                    self.drinks[iddrink].create_version(shortname=version["shortname"], ingredients=version_ings,
                                                        proportions=version["proportions"], glassize=version["glassize"])
            print("Reloading done!")
            return 0
        except:
            print("Could not reload from json. Something went wrong..")
            return 1