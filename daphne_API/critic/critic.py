import csv
import json
import string
import numpy as np
from sqlalchemy.orm import sessionmaker

import daphne_API.historian.models as models
import daphne_API.problem_specific as problem_specific

class CRITIC:

    def __init__(self, problem):
        # Connect to the CEOS database
        self.engine = models.db_connect()
        self.session = sessionmaker(bind=self.engine)()
        self.instruments_dataset = problem_specific.get_instrument_dataset(problem)
        self.orbits_dataset = problem_specific.get_orbit_dataset(problem)


    def get_missions_from_genome(self, problem_type, genome):
        missions = []
        if problem_type == 'binary':
            missions = self.get_missions_from_bitstring(genome)
        elif problem_type == 'discrete':
            missions = self.get_missions_from_partition(genome)

        return missions

    def get_missions_from_bitstring(self, bitstring):
        missions = []
        num_instr = len(self.instruments_dataset)
        num_orbits = len(self.orbits_dataset)
        for orbit in range(num_orbits):
            mission = { "orbit": self.orbits_dataset[orbit]["name"], "instruments": [] }

            for instr in range(num_instr):
                idx = orbit*num_instr + instr
                if bitstring[idx]:
                    mission["instruments"].append(self.instruments_dataset[instr])

            missions.append(mission)

        return missions

    def get_missions_from_partition(self, genome):
        missions = []
        # TODO: Retrieve all missions from genome

        return missions


    def orbits_similarity(self, mission_orbit, hist_mission):
        score = 0
        # Score orbit type
        if mission_orbit["type"] == hist_mission.orbit_type:
            score += 1
        # Score orbit altitude
        if hist_mission.orbit_altitude_num is not None and \
                                        mission_orbit["altitude"] - 50 < hist_mission.orbit_altitude_num < mission_orbit["altitude"] + 50:
            score += 1
        # Score orbit LST
        if mission_orbit["LST"] == hist_mission.orbit_LST:
            score += 1
        # Return orbit score
        return score

    def instruments_score(self, mission_instrument, hist_instrument):
        score = 0.0
        # Score instrument type
        for type2 in hist_instrument.types:
            if mission_instrument["type"] == type2.name:
                score += 1
                break
        # Score instrument technology
        if mission_instrument["technology"] == hist_instrument.technology:
            score += 1
        # Score instrument geometry
        for geometry2 in hist_instrument.geometries:
            if mission_instrument["geometry"] == geometry2.name:
                score += 1
                break
        # Score instrument wavebands
        for waveband1 in mission_instrument["wavebands"]:
            for waveband2 in hist_instrument.wavebands:
                if waveband1 == waveband2.name:
                    score += 1/len(mission_instrument["wavebands"])
                    break
        # Return instruments score
        return score

    def instruments_similarity(self, instruments1, instruments2):
        score = 0.0
        # Compute similarity matrix
        N = max(len(instruments1), len(instruments2))
        sim = np.zeros((N, N))
        for i1 in range(len(instruments1)):
            for i2 in range(len(instruments2)):
                sim[i1, i2] = self.instruments_score(instruments1[i1], instruments2[i2])
        # Find the best matches for i1xi2 (greedy)
        for k in range(len(instruments1)):
            i1i2 = np.argmax(sim)
            i1 = int(i1i2 / N)
            i2 = i1i2 % N
            score += sim[i1, i2]/len(instruments1)
            sim[i1, :] = 0
            sim[:, i2] = 0
        return score


    def missions_similarity(self, mission_orbit, mission_instruments, missions_database):
        max_score = -1
        max_mission = None
        # Iterate over all the missions in the database
        for hist_mission in missions_database:
            score = 0
            # Get orbits similarity
            score += self.orbits_similarity(mission_orbit, hist_mission)
            # If score bigger than a threshold
            if(score > 1):
                # Get instruments similarities
                score += self.instruments_similarity(mission_instruments, hist_mission.instruments)
            if score > max_score:
                max_score = score
                max_mission = hist_mission
        # Return result
        return [(max_score*10)/7, max_mission]


    def historian_critic(self, problem_type, arch):
        result = []
        # Convert architecture format
        missions = self.get_missions_from_genome(problem_type, arch)

        # Type 2: Mission by mission
        missions_database = self.session.query(models.Mission)
        for mission in missions:
            # Find the orbit information based in the name
            orbit_info = {}
            for orbit in self.orbits_dataset:
                if orbit["name"] == mission["orbit"]:
                    orbit_info = orbit
                    break

            # Find similar past missions from the information on the current mission, including orbit and instruments
            res = self.missions_similarity(orbit_info, mission["instruments"], missions_database)
            if len(mission["instruments"]) > 0:
                if res[0] < 6:
                    result.append("No past mission is similar to your satellite in orbit %s. Consider changing it." % \
                                  mission["orbit"])
                else:
                    result.append("A past mission is really similar to your design in orbit %s: %s. You can probably focus on other orbits for now." % \
                                  (mission["orbit"], res[1].name))
                        # +
                        # '<br>'.join(["Instrument similar to %s (score: %.2f)" % \
                        #    (i[0], i[2]) for i in self.instruments_match_dataset(res[1].instruments)]) + '.')
        return result


    def criticize_arch(self, problem_type, arch):
        result = []
        # Type 1: Instrument by intrument
        #for o in range(len(arch)):
        #    for i in arch[o]:
        #        orbit = self.orbitsDataset[o]
        #        instrument = next(ii for ii in self.instrumentsDataset if ii["alias"] == i)
        #        res = self.getSimilarInstruments(orbit, instrument)
        #        if len(res) == 0:
        #            result.append([
        #                "historian1",
        #                "Instrument %s has never been flown in orbit %s before" % \
        #                     (instrument["alias"], orbit["alias"])
        #            ])
        #        else:
        #            result.append([
        #                "historian1",
        #                "Instrument %s has been flown in orbit %s before (%s matches in the database)" % \
        #                    (instrument["alias"], orbit["alias"], len(res)),
        #                str(', '.join([r.name for r in res]))
        #        ])
        
        
        # Type 2: Mission by mission
        historian_results = self.historian_critic(problem_type, arch)
        for hist in historian_results:
            result.append({
                "type": "Historian",
                "advice": hist
            })

        # Return result
        return result
