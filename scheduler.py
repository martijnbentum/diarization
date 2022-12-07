import time
import threading

class scheduler:
    '''Create an object that holds every which performs a task every n units
    given certain conditions.
    The tasks are performed in a seperate thread.
    Multiple tasks can be added to the scheduler
    '''
    def __init__(self,name = 'default'):
        self.name = name
        self.everies= []

    def add_every(self,interval = 1, unit = 'second',conditions = [],
        function = None, name = 'default', args = ()):
        '''Add a task to the scheduler.'''
        self.everies.append(every(interval,unit,conditions,function,
            name,args))



class every:
    '''Create an object that performs a task every n units given 
    certain conditions.
    The task is performed in a seperate thread.
    '''
    def __init__(self,interval = 1, unit = 'second',conditions = [], 
        function = None,name='default',args = (), kwargs = {},
        maximum_nexecuters=10, n_times = None, verbose = False):
        '''A task is performed by providing a function interval and units.
        interval        number of units to wait between function calls.
        unit            time is unit times interval
        conditions      the conditions when the function is executed every  
                        n units, ie weekdays
        function        the task to be performed as declared in a function
        name            name of the every
        args            arguments to be past to the function
        kwargs          keyword argument dictionary to be passed to the 
                        function
        maximum_...     if the task is longer than the interval, 
                        this will cap the number of executers
        '''
        self.interval = interval
        self.unit2seconds = make_unit2seconds()
        if not unit in self.unit2seconds.keys():
            print(unit,'not recognized, using default: seconds')
            unit = 'second'
        self.unit = unit
        self.conditions = conditions
        self.interval_seconds = self.interval * self.unit2seconds[unit]
        if function == None: self.function = self.set_interval_reached()
        self.function = function
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.executers = []
        self.maximum_nexecuters = maximum_nexecuters
        self.n_times = n_times
        self.verbose = verbose
        self.n_times_counter = 1
        self.interval_reached = False
        self.wait(self.interval_seconds)

    def check_conditions(self):
        '''Check whether the conditions are true 
        (if conditions every performs task every n units).'''
        n_con = len(self.conditions)
        if n_con > 2: print('probably to many conditions',self.conditions)
        if n_con == 2 and 'weekday' not in self.conditions: 
            if 'weekend' not in self.conditions: 
                print('multiple conditions should contain weekend or weekday',
                    self.conditions)
        self.seconds_to_conditions_met = 0
        for condition in self.conditions:
            self.seconds_to_conditions_met += time2(condition)
        if self.seconds_to_conditions_met == 0: self.conditions_met = True
        else: self.conditions_met = False
        if self.verbose:
            print('seconds to conditions met:',self.seconds_to_conditions_met,
                'conditions:',self.conditions)

    def run(self):
        '''Run the every no blocking, ie in a seperate thread.'''
        self.check_conditions()
        self.remove_finished_executers()
        if not self.conditions_met:
            if self.verbose:
                print('waiting for conditions to be met:',self.conditions,
                    self.seconds_to_conditions_met)
            # self.wait(int(self.seconds_to_conditions_met/100))
            self.wait(10)
        elif len(self.executers) >= self.maximum_nexecuters:
            if self.verbose:
                print('waiting to execute funciton, maximum nexecuters is reached:',
                    self.maximum_nexecuters)
            if self.interval_seconds < 1: self.wait(self.interval_seconds)
            else: self.wait(1)
        elif self.n_times != None and self.n_times_counter > self.n_times:
            self.stop()
        else:
            if self.verbose:
                print('executing function:',self.function,
                    'if none setting interval_reached to true.')
            self.execute()

    def stop(self):
        '''Stop executing function calls.'''
        self.waiter.cancel()
        self.executers = []

    def wait(self,wait):
        '''Wait until the interval is over to do a condition check and function call.'''
        self.waiter = threading.Timer(wait,self.run)
        self.waiter.start()

    def execute(self):
        '''Start a thread to run the function call after appropiate wait time.'''
        self.n_times_counter +=1
        e = threading.Thread(target= self.function,args=self.args,kwargs=self.kwargs)
        e.start()
        self.executers.append(e)
        self.wait(self.interval_seconds)

    def remove_finished_executers(self):
        '''If a thread has called the function do a clean up.'''
        temp = []
        for executer in self.executers:
            if executer.is_alive():
                temp.append(executer)
        self.executers = temp


def make_unit2seconds():
    day = 24*3600
    return {
        'second':1,
        'minute':60,
        'hour':3600,
        'day':day,
        'week':7*day,
        'month':30*day,
        'year':365*day}


def get_dayname(t = None):
    if t == None: t = time.time()
    return time.strftime('%A', time.localtime(t))


def is_day_of_week(name,t= None):
    if t == None: t = time.time()
    return name == time.strftime('%A', time.localtime(t))


def is_weekend(t = None):
    if t == None: t = time.time()
    if get_dayname(t) in ['Saturday','Sunday']: return True
    else: return False


def is_weekday(t = None):
    if t == None: t = time.time()
    return not is_weekend(t)


def is_day(t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if h >= 600 and h < 1800: return True
    else: return False


def is_night(t = None):
    if t == None: t = time.time()
    return not is_day(t)


def is_morning(t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if h >= 600 and h < 1200: return True
    else: return False


def is_afternoon(t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if h >= 1200 and h < 1800: return True
    else: return False


def is_evening(t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if h >= 1800: return True
    else: return False


def is_deepnight(t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if h < 600: return True
    else: return False


def is_between(start,end, t = None):
    if t == None: t = time.time()
    h = int(time.strftime('%H%M', time.localtime(t)))
    if start < end: return h >= start and h < end
    else: return h >= start or h < end

# Time to functions

def h2s(h):
    '''transform hours to seconds. '''
    if len(str(h)) > 2: return int(h/100) * 3600 + h%100 * 60
    else: return h * 60


def s2h(s):
    '''Transform seconds to hours. '''
    h = int(s/3600) * 100
    s = s%3600
    h += int(s/60)
    return h

def make_weekday_names2n():
    '''Dict to transelate weekday name to number.'''
    return {
        'Sunday':0,
        'Monday':1,
        'Tuesday':2,
        'Wednesday':3,
        'Thursday':4,
        'Friday':5,
        'Saturday':6}


def time2(moment = 'day',t = None):
    '''Check how much until certain moment (condition).'''
    if t == None: t = time.time()
    weekday_names2n = make_weekday_names2n()
    h = int(time.strftime('%H%M', time.localtime(t)))
    s = h2s(h)
    if moment == 'day':
        if is_day(t): return 0
        if h >= 1800: rs = h2s(3000) - s
        else: rs = h2s(600) - s
    elif moment == 'night':
        if is_night(t): return 0
        rs = h2s(1800) - s
    elif moment == 'morning':
        if is_morning(t): return 0
        if h >= 1200: rs = h2s(3000) - s
        else: rs = h2s(600) - s
    elif moment == 'afternoon':
        if is_afternoon(t): return 0
        if h >= 1800: rs = h2s(3600) - s
        else: rs = h2s(1200) - s
    elif moment == 'evening':
        if is_evening(t): return 0
        rs = h2s(1800) - s
    elif moment == 'deepnight' or moment == 'tomorrow':
        if is_deepnight(t): return 0
        rs = h2s(2400) - s
    elif moment == 'weekday':
        if is_weekday(t): return 0
        if get_dayname(t) == 'Saturday': rs = h2s(4800) - s
        else: rs = h2s(2400) - s
    elif moment == 'weekend':
        if is_weekend(t): return 0
        day_number = int(time.strftime('%w', time.localtime(t)))
        rs = h2s((6 - day_number) * 2400) - s
    elif moment in weekday_names2n.keys():
        tname = time.strftime('%A', time.localtime(t))
        if tname == moment: return 0
        tnumber = weekday_names2n[tname] + 1
        namenumber = weekday_names2n[moment] + 1
        if namenumber<tnumber: dif = 7 - namenumber - 1
        else: dif = namenumber - tnumber - 1
        print(dif,tnumber,namenumber)
        rs = h2s(dif * 2400) + h2s(2400) - s
    elif type(moment) == tuple and len(moment) == 2 and type(moment[0]) == int:
        start, end = moment
        if is_between(start,end,t): return 0
        if end > start and h >= end: rs = h2s(2400 + start) - s
        else: rs = h2s(start) - s
    else:
        print(moment, 'is not defined, return 0')
    return rs


def print_time():
    '''Print current time.'''
    print('time is now:',int(time.strftime('%H%M', time.localtime(time.time()))),
        time.time())
