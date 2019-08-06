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
    MEAN_CUSTOMER_ARRIVAL_RATE_PER_MIN = 4
    SD_CUSTOMER_ARRIVAL_RATE_PER_MIN = 2

    MEAN_UNITS_OF_WORK_PER_CUSTOMER = 8
    SD_UNITS_OF_WORK_PER_CUSTOMER = 6

    NUM_SERVERS = 4
    MEAN_UNITS_OF_WORK_PER_SERVER_PER_MIN = 14
    SD_UNITS_OF_WORK_PER_SERVER_PER_MIN = 4

    HOURS_TO_RUN = 8
    MINUTES_TO_RUN = HOURS_TO_RUN * 60

class Simulation:
    """
    The main class used to run the simulation of customers being serviced by cashiers at a store.
    ...

    Methods
    -------
    run()
        A class method used to run the simulation, creates all the cashiers needed anda line with
        those cashiers, and then iterates through the amount of minutes specified in the Parameters class
        and simulates the arrival of new customers and the processing of those customers each minute
    """

    def run():
        cashiers = Server.getServers(
            Parameters.NUM_SERVERS,
            Parameters.MEAN_UNITS_OF_WORK_PER_SERVER_PER_MIN,
            Parameters.SD_UNITS_OF_WORK_PER_SERVER_PER_MIN)

        line = CustomerLine(cashiers)
        for minute in range(Parameters.MINUTES_TO_RUN):
            customers = Customer.newCustomers(
                minute,
                Parameters.MEAN_CUSTOMER_ARRIVAL_RATE_PER_MIN,
                Parameters.SD_CUSTOMER_ARRIVAL_RATE_PER_MIN,
                Parameters.MEAN_UNITS_OF_WORK_PER_CUSTOMER,
                Parameters.SD_UNITS_OF_WORK_PER_CUSTOMER)

            line.process(customers, minute)

        #print("Service Times", Customer.ServiceTimes)
        print("Customers finished", Customer.TotalFinished)
        print("Number of customers still in line", line.size())
        print(
            "Average Wait Time",
            sum(Customer.ServiceTimes) / len(Customer.ServiceTimes),
            "Minutes")



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

    def __init__(self, _cashiers):
        self.cashiers = _cashiers
        self.customerQueue = deque()

    def process(self, customers: list, time: int):
        self.customerQueue += customers

        for cashier in self.cashiers:
            if self.customerQueue and cashier.isIdle():
                cashier.customer = self.customerQueue.popleft()

            cashier.process(time)

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
    getServers(numServers, avgWorkPerMin, sdOfWorkPerMin)
        a class method that creates the number of cashiers requested with a given mean and standard
        deviation for work per minute

    isIdle(self)
        returns whether or not the cashier is free to take another customer or not

    process(self, currentTime)
        simulates 1 minute of time for the cashier, where if a customer is assigned to this cashier
        the cashier will make progress on servicing that customer
    """

    def __init__(self, _workPerMin: float):
        self.unitsOfWorkPerMin =_workPerMin
        self.customersServed = 0
        self.customer = None

    def getServers(numServers, avgWorkPerMin, sdOfWorkPerMin):
        workerSpeeds = np.random.normal(avgWorkPerMin, sdOfWorkPerMin, numServers)
        return [Server(abs(workerSpeed)) for workerSpeed in workerSpeeds]

    def isIdle(self):
        return self.customer == None

    def process(self, currentTime):
        if not self.customer:
            return

        workRemaining = self.customer.help(self.unitsOfWorkPerMin, currentTime)
        if workRemaining <= 0:
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
    numCustomerArrivalsThisMinute(time, arrivalRate, arrivalSD, workPerCustomerAvg, workPerCustomerSD)
        a class method that creates the number of cashiers requested with a given mean and standard
        deviation for work per minute

    newCustomers(timeNow, arrivalRate, arrivalSD, workPerCustomerAvg, workPerCustomerSD)
        instantiates a number of customers based on the Parameters class, with each customer in need
        of some units of work

    help(self, workCompleted, timeNow)
        complete some of the customers work and return the work remaining (0 or negative if
        work is complete)
    """

    ServiceTimes = []
    TotalFinished = 0

    def __init__(self, _unitsOfWork, _time):
        self.unitsOfWorkToComplete = _unitsOfWork
        self.workRemaining = _unitsOfWork
        self.timeEnteredLine = _time

    def numCustomerArrivalsThisMinute(customersPerMinAvg, customersPerMinSd):
        arrivals = np.random.normal(customersPerMinAvg, customersPerMinSd, 1)
        return abs(int(arrivals[0]))

    def newCustomers(timeNow, arrivalRate, arrivalSD, workPerCustomerAvg, workPerCustomerSD):
        numArrivals = Customer.numCustomerArrivalsThisMinute(arrivalRate, arrivalSD)
        workPerCustomer = np.random.normal(workPerCustomerAvg, workPerCustomerSD, numArrivals)

        return [Customer(abs(work), timeNow) for work in workPerCustomer]

    def help(self, workCompleted, timeNow):
        self.workRemaining -= workCompleted
        if self.workRemaining <= 0:
            serviceTime = timeNow - self.timeEnteredLine
            Customer.ServiceTimes.append(serviceTime)
            Customer.TotalFinished += 1

        return self.workRemaining


Simulation.run()
