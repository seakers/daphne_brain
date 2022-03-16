import EOSS.historian.models as models
import numpy as np
from sqlalchemy.orm import sessionmaker
from EOSS.vassar.interface.ttypes import MissionMeasurements

import logging

logger = logging.getLogger('EOSS.historian')


class Historian:

    def __init__(self):
        # Connect to the CEOS database
        self.engine = models.db_connect()
        self.session = sessionmaker(bind=self.engine)()

    def get_all_missions(self):
        missions = []
        missions_database = self.session.query(models.Mission)
        #logger.exception("Missions: {0}".format(missions_database))
        for mission in missions_database:
            missions.append(mission.name)
        return missions

    def get_all_mission_measurements(self):
        missions_database = self.session.query(models.Mission)
        collection = []
        for mission in missions_database:
            mission_measurements = []
            if mission.launch_date is None:
                continue
            start_date = int(mission.launch_date.strftime("%Y"))
            end_date = int(mission.eol_date.strftime("%Y"))
            instruments = mission.instruments
            for instrument in instruments:
                measurements = instrument.measurements
                for measurement in measurements:
                    mission_measurements.append(measurement.name)
            collection.append(MissionMeasurements(mission_measurements, start_date, end_date))
        return collection

    def data_continuity_table(self):
        missions_database = self.session.query(models.Mission)
        quantities = []
        measurement_list = []
        start_dates = []
        end_dates = []
        for mission in missions_database:
            if mission.launch_date is None:
                continue
            start_date = int(mission.launch_date.strftime("%Y"))
            end_date = int(mission.eol_date.strftime("%Y"))
            for instrument in mission.instruments:
                for measurement in instrument.measurements:
                    if(measurement.name not in measurement_list):
                        measurement_list.append(measurement.name)
                        start_dates.append(start_date)
                        end_dates.append(end_date)

        measurement_array = []
        xd = np.zeros(shape=(len(measurement_list), 100))
        for i in range(0, len(measurement_list)):
            for j in range(0, 100):
                # for measurement in measurement_list:
                    
                for mission in missions_database:
                    if mission.launch_date is None:
                        continue
                    start_date = int(mission.launch_date.strftime("%Y"))
                    end_date = int(mission.eol_date.strftime("%Y"))
                    for instrument in mission.instruments:
                        for measurement in instrument.measurements:
                            if(measurement.name == measurement_list[i] and j+1950 >= start_date and j+1950 <= end_date):
                                xd[i][j] = xd[i][j] + 1
        return measurement_list, xd


