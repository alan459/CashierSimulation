import numpy as np
from collections import deque

class Parameters:
    """
    A class for specifying the parameters of the simulation, such as customer arrival rates per minute,
    workload per customer, efficiency of cashiers, number of cashiers, and time to run the simulation.
    ...

    Attributes
    ----------
    MEAN_CUSTOMER_ARRIVAL_RATE_PER_MIN, SD_CUSTOMER_ARRIVAL_RATE_PER_MIN
        Mean and standard deviation for customer arrival rate, fed into a normal distribution function
        to get the amount of customers arriving for a given minute in the simulation

    MEAN_UNITS_OF_WORK_PER_CUSTOMER, SD_UNITS_OF_WORK_PER_CUSTOMER
        Mean and standard deviation for units of work to be done per customer, fed into a normal
        distribution function to generate the amount of work for a given customer

    MEAN_UNITS_OF_WORK_PER_SERVER_PER_MIN, SD_UNITS_OF_WORK_PER_SERVER_PER_MIN
        Mean and standard deviation for units of work a cashier gets done per minute, fed into a normal
        distribution function to generate the cashiers based on these statistics

    NUM_SERVERS
        Number of cashiers to handle customers in this simulation

    HOURS_TO_RUN, MINUTES_TO_RUN
        The number of hours to run the simulation, which get fed into minutes to run which will contain
        the total amount of minutes to run the simulation for
    """
    MEAN_CUSTOMER_ARRIVAL_RATE_PER_MIN = 8
    SD_CUSTOMER_ARRIVAL_RATE_PER_MIN = 2

    MEAN_UNITS_OF_WORK_PER_CUSTOMER = 10
    SD_UNITS_OF_WORK_PER_CUSTOMER = 4

    NUM_SERVERS = 4
    MEAN_UNITS_OF_WORK_PER_SERVER_PER_MIN = 15
    SD_UNITS_OF_WORK_PER_SERVER_PER_MIN = 5

    HOURS_TO_RUN = 3
    MINUTES_TO_RUN = HOURS_TO_RUN * 60

    LINE_CAP = 10


class SimulationEngine:
    """
    Used to generate cashiers and customers in the simulation. Uses the Parameters class for
    mean and standard deviation of values related to generating cashiers and customers.
    ...

    Methods
    -------
    generateCashiers()
        a class method that creates the number of cashiers requested with a given mean and standard
        deviation for work per minute

    generateCustomerArrivals(time)
        a class method that creates the number of cashiers requested with a given mean and standard
        deviation for work per minute from the Parameters class

    newCustomers(timeNow)
        instantiates a number of customers based on the Parameters class, with each customer in need
        of some units of work
    """
    @staticmethod
    def generateCashiers():
        workerSpeeds = np.random.normal(
            Parameters.MEAN_UNITS_OF_WORK_PER_SERVER_PER_MIN,
            Parameters.SD_UNITS_OF_WORK_PER_SERVER_PER_MIN,
            Parameters.NUM_SERVERS)

        return [Server(abs(workerSpeed)) for workerSpeed in workerSpeeds]

    @staticmethod
    def generateCustomerArrivals():
        arrivals = np.random.normal(
            Parameters.MEAN_CUSTOMER_ARRIVAL_RATE_PER_MIN,
            Parameters.SD_CUSTOMER_ARRIVAL_RATE_PER_MIN,
            1)
        return abs(int(arrivals[0]))

    @staticmethod
    def newCustomers(timeNow):
        numArrivals = SimulationEngine.generateCustomerArrivals()

        workPerCustomer = np.random.normal(
            Parameters.MEAN_UNITS_OF_WORK_PER_CUSTOMER,
            Parameters.SD_UNITS_OF_WORK_PER_CUSTOMER,
            numArrivals)

        return [Customer(abs(work), timeNow) for work in workPerCustomer]

class SimulationManager:
    """
    The main class used to run the simulation of customers being serviced by cashiers at a store.
    ...

    Methods
    -------
    run()
        A class method used to run the simulation, creates all the cashiers needed anda line with
        those cashiers, and then iterates through the amount of minutes specified in the Parameters class
    """

    @staticmethod
    def run():
        cashiers = SimulationEngine.generateCashiers()

        line = CustomerLine(cashiers, Parameters.LINE_CAP)
        for minute in range(Parameters.MINUTES_TO_RUN):
            customers = SimulationEngine.newCustomers(minute)

            line.process(customers, minute)

        #print("Service Times", Customer.ServiceTimes)
        Customer.printStatistics()
        print("Number of customers still in line", line.size())
        print("Customers Lost,", CustomerLine.CustomersLost)




class CustomerLine:
    """
    A class used to represent a line of customers waiting for service and a list of cashiers that
    provide service.
    ...

    Attributes
    ----------
    cashiers : list[Server]
        a list of cashiers that handle this line
    customerQueue : list[Customer]
        a list used as a queue to represent customers in line

    Methods
    -------
    process(customers, time)
        Simulates 1 unit of time (in this case 1 minute), where each cashier makes progress on their
        current customer and gets assigned a new one from the customer queue if they're idle

    size(self)
        Returns the size of the line
    """

    CustomersLost = 0


    def __init__(self, _cashiers, _cap):
        self.cashiers = _cashiers
        self.customerQueue = deque()
        self.cap = _cap


    def process(self, customers, timeNow):

        self.addCustomersToLine(customers)
        self.workOnCustomers(timeNow)


    def addCustomersToLine(self, customers):
        # check if adding new customers will put line size over capacity and add them so that capacity isn't exceeded
        if len(self.customerQueue) + len(customers) <= self.cap:
            self.customerQueue += customers
        else:
            customersToAdd = self.cap - len(self.customerQueue)
            CustomerLine.CustomersLost += len(customers) - customersToAdd

            for i in range(customersToAdd):
                self.customerQueue.append(customers[i])


    def workOnCustomers(self, timeNow):
        for cashier in self.cashiers:
            while self.customerQueue and cashier.canDoMoreWorkThisMinute(timeNow):
                if cashier.isIdle():
                    cashier.assignCustomer(self.customerQueue.popleft(), timeNow)

                cashier.process(timeNow)


    def size(self):
        return len(self.customerQueue)


class Server:
    """
    A class used to represent a server/cashier at a store servicing customers.
    ...

    Attributes
    ----------
    unitsOfWorkPerMin : double
        the amount of work a server can do in 1 minute
    customer : Customer
        the customer currently being serviced by this cashier
    customersServed : int
        the amount of customers finished being serviced by this cashier

    Methods
    -------
    isIdle(self)
        returns whether or not the cashier is free to take another customer or not

    process(self, currentTime)
        simulates 1 minute of time for the cashier, where if a customer is assigned to this cashier
        the cashier will make progress on servicing that customer

    canDoMoreWorkThisMinute(self, timeNow)
        returns a boolean to indicate whether or not this cashier has used up all of their units of work
        for this minute in the simulation

    assignCustomer(self, customer, timeNow)
        assigns the customer to the cashier and calls a method to indicate that the customer is no longer
        waiting in the queue to record the waiting time
    """

    def __init__(self, _workPerMin):
        self.unitsOfWorkPerMin =_workPerMin
        self.workDoneInLastMin = 0
        self.lastCustomerTime = -1
        self.customersServed = 0
        self.customer = None

    def isIdle(self):
        return self.customer == None

    def canDoMoreWorkThisMinute(self, timeNow):
        return self.lastCustomerTime < timeNow or self.workDoneInLastMin < self.unitsOfWorkPerMin

    def assignCustomer(self, customer, timeNow):
        customer.finishedWaiting(timeNow)
        self.customer = customer

    def process(self, currentTime):
        if not self.customer:
            return

        # reset work done this minute if this is first time method is being called for this time
        if self.lastCustomerTime < currentTime:
            self.workDoneInLastMin = 0
            self.lastCustomerTime = currentTime

        workToBeDone = min(
            self.customer.workRemaining,
            self.unitsOfWorkPerMin - self.workDoneInLastMin)

        self.customer.help(workToBeDone, currentTime, workToBeDone / self.unitsOfWorkPerMin)
        self.workDoneInLastMin += workToBeDone

        if self.customer.isFinished():
            self.customer = None
            self.customersServed += 1

class Customer:
    """
    A class used to represent a customer at a store obtaining service from a cashier.
    ...

    Attributes
    ----------
    ServiceTimes : list[int]
        a class variable storing the amount of time each customer spent between entering the queue
        and completion of service
    unitsOfWorkToComplete : double
        the initial amount of work the customer needs completed by a cashier
    workRemaining : double
        the remaining amount of work the customer needs completed by a cashier
    timeEnteredLine : int
        the second at which the customer got in line

    Methods
    -------
    help(self, workCompleted, timeNow)
        complete some of the customers work and return the work remaining (0 or negative if
        work is complete)

    finishedWaiting(self, currentTime)
        for indicating that the customer has finished waiting in the queue for service and saving
        time waited into WaitingTimes

    isFinished(self)
        inidicates if the customer has finished getting service
    """

    WaitingTimes = []
    ServiceTimes = []
    TotalFinished = 0

    def __init__(self, _unitsOfWork, _time):
        self.unitsOfWorkToComplete = _unitsOfWork
        self.workRemaining = _unitsOfWork
        self.timeEnteredLine = _time
        self.timeExitedLine = -1

    def help(self, workCompleted, timeNow, percentOfMinuteHelped):
        self.workRemaining -= workCompleted
        if self.workRemaining <= 0:
            # need to add fraction of current minute to get total service time for customer
            serviceTime = timeNow - self.timeExitedLine + percentOfMinuteHelped

            Customer.ServiceTimes.append(serviceTime)
            Customer.TotalFinished += 1

    def isFinished(self):
        return self.workRemaining <= 0

    def finishedWaiting(self, currentTime):
        self.timeExitedLine = currentTime
        Customer.WaitingTimes.append(self.timeExitedLine - self.timeEnteredLine)

    @staticmethod
    def printStatistics():
        print("Customers finished", Customer.TotalFinished)
        print(
            "Average Wait Time",
            sum(Customer.WaitingTimes) / len(Customer.WaitingTimes),
            "Minutes")

        print(
            "Average Service Time",
            sum(Customer.ServiceTimes) / len(Customer.ServiceTimes),
            "Minutes")


SimulationManager.run()
