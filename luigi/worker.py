import scheduler, central_planner

class Worker(object):
    """ Worker object communicates with a scheduler.

    Simple class that talks to a scheduler and:
    - Tells the scheduler what it has to do + its dependencies
    - Asks for stuff to do (pulls it in a loop and runs it)
    """
    def __init__(self, sch=None, locally=False):
        if sch:
            self.__scheduler = sch
            self.__pass_exceptions = True
        elif locally:
            self.__scheduler = central_planner.CentralPlannerScheduler()
            self.__pass_exceptions = True
        else:
            self.__scheduler = scheduler.RemoteScheduler()
            self.__pass_exceptions = False

        self.__scheduled_tasks = {}
    
    def add(self, task):
        s = str(task)
        if s in self.__scheduled_tasks: return
        self.__scheduled_tasks[s] = task

        if task.complete():
            self.__scheduler.add_task(s, status='DONE')
            return

        elif task.run == NotImplemented:
            self.__scheduler.add_task(s, status='BROKEN')
            return

        else:
            self.__scheduler.add_task(s, status='PENDING')

            for task_2 in task.deps():
                s2 = str(task_2)
                self.add(task_2) # Schedule it recursively
                self.__scheduler.add_dep(s, s2)

    def run(self):
        while True:
            done, s = self.__scheduler.get_work()
            if done: break

            if s == None: break

            task = self.__scheduled_tasks[s]

            # TODO: we should verify that all dependencies exist (can't trust the scheduler all the time)
            try:
                task.run()            
                status, expl = 'DONE', None
            except KeyboardInterrupt:
                raise
            except:
                if self.__pass_exceptions: raise # TODO: not necessarily true that we want to break on the first exception

                import sys, traceback
                
                status = 'FAILED'
                d = [sys.exc_info()[0], sys.exc_info()[1], traceback.format_exc(sys.exc_info()[2])]
                expl = '\n'.join(map(str, d))
                print expl

            self.__scheduler.status(s, status=status, expl=expl)
