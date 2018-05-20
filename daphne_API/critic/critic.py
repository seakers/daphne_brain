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


    # Used to compute CRITIC1.csv

    def get_arnau_format(self, bitstring):
        arch_critic = []
        num_instr = len(self.instruments_dataset)
        num_orbits = len(self.orbits_dataset)
        for orbit in range(num_orbits):
            arch_critic.append(''.join([string.ascii_uppercase[instr - num_instr*orbit] for instr in range(num_instr*orbit, num_instr*(orbit + 1)) if bitstring[instr]]))
        return arch_critic

    def get_similar_instruments(self, orbit, instrument):
        # Get instruments with similar characteristics and similar orbits
        query = self.session.query(models.Instrument) \
            .filter(models.Instrument.types.any(models.InstrumentType.name == instrument["type"])) \
            .filter(models.Instrument.technology == instrument["technology"]) \
            .filter(models.Instrument.geometries.any(models.GeometryType.name == instrument["geometry"])) \
            .filter(models.Instrument.wavebands.any(models.Waveband.name.in_(instrument["wavebands"]))) \
            .filter(models.Instrument.missions.any(models.Mission.orbit_type == orbit["type"])) \
            .filter(models.Instrument.missions.any(models.Mission.orbit_altitude.between(orbit["altitude"] - 50,
                                                                                         orbit["altitude"] + 50))) \
            .filter(models.Instrument.missions.any(models.Mission.orbit_LST == orbit["LST"]))
        # Return result
        result = query.all()
        return result

    # Used to compute CRITIC2.csv

    def orbits_similarity(self, orbit1, mission2):
        score = 0
        # Score orbit type
        if orbit1["type"] == mission2.orbit_type:
            score += 1
        # Score orbit altitude
        if mission2.orbit_altitude_num is not None and \
                                        orbit1["altitude"] - 50 < mission2.orbit_altitude_num < orbit1["altitude"] + 50:
            score += 1
        # Score orbit LST
        if orbit1["LST"] == mission2.orbit_LST:
            score += 1
        # Return orbit score
        return score

    def instruments_score(self, instrument1, instrument2):
        score = 0.0
        # Score instrument type
        for type2 in instrument2.types:
            if instrument1["type"] == type2.name:
                score += 1
                break
        # Score instrument technology
        if instrument1["technology"] == instrument2.technology:
            score += 1
        # Score instrument geometry
        for geometry2 in instrument2.geometries:
            if instrument1["geometry"] == geometry2.name:
                score += 1
                break
        # Score instrument wavebands
        for waveband1 in instrument1["wavebands"]:
            for waveband2 in instrument2.wavebands:
                if waveband1 == waveband2.name:
                    score += 1/len(instrument1["wavebands"])
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

    def instruments_match_dataset(self, instruments2):
        matches = []
        instruments1 = self.instruments_dataset
        N = len(instruments1)
        M = len(instruments2)
        # Compute similarity matrix
        sim = np.zeros((N,M))
        for i1 in range(N):
            for i2 in range(M):
                sim[i1,i2] = self.instruments_score(instruments1[i1], instruments2[i2])*10/4
        # Find the best matches for i2
        for i2 in range(M):
            i1i2 = np.argmax(sim[:,i2])
            i1 = i1i2 % N
            matches.append([instruments1[i1]["alias"], instruments2[i2].name, sim[i1,i2]])
        return matches

    def missions_similarity(self, orbit1, instruments1, missions_database):
        max_score = -1
        max_mission = None
        # Iterate over all the missions in the database
        for mission2 in missions_database:
            score = 0
            # Get orbits similarity
            score += self.orbits_similarity(orbit1, mission2)
            # If score bigger than a threshold
            if(score > 1):
                # Get instruments similarities
                score += self.instruments_similarity(instruments1, mission2.instruments)
            if score > max_score:
                max_score = score
                max_mission = mission2
        # Return result
        return [(max_score*10)/7, max_mission]

    def match_features(self, arch):
        res = []
        with open("./daphne_API/critic/EOSS_features.csv", "r") as csvfile:
            features = csv.reader(csvfile, delimiter=':')
            for row in features:
                match = True
                # present
                for i in row[0]:
                    if not any(i in o for o in arch):
                        match = False
                # absent
                for i in row[1]:
                    if any(i in o for o in arch):
                        match = False
                # inOrbit
                inOrbit = json.loads(row[2])
                for o in range(len(inOrbit)):
                    for i in inOrbit[o]:
                        if not i in arch[o]:
                            match = False
                # notInOrbit
                notInOrbit = json.loads(row[3])
                for o in range(len(notInOrbit)):
                    for i in notInOrbit[o]:
                        if i in arch[o]:
                            match = False
                # together
                if len(row[4]) > 1:
                    for o in range(len(arch)):
                        if row[4][0] in arch[o]:
                            if not [c in arch[o] for c in row[4]]:
                                match = False
                # togetherInOrbit
                rr = json.loads(row[5])
                if int(rr[1]) > 0:
                    if len(rr[0]) > 1:
                        if rr[0] in arch(int(rr[1]-1)):
                            if not [c in arch[int(rr[1]-1)] for c in rr[0]]:
                                match = False
                # separate
                if len(row[6]) > 1:
                    for o in range(len(arch)):
                        if row[6][0] in arch(o):
                            if [c in arch[o] for c in row[6]]:
                                match = False
                # emptyOrbit
                emptyOrbit = int(row[7])-1
                if emptyOrbit > -1:
                    if arch[emptyOrbit] != '':
                        match = False
                # numberOfOrbitsUsed
                numberOfOrbitsUsed = int(row[8])
                if numberOfOrbitsUsed != -1:
                    if sum(o != '' for o in arch) != numberOfOrbitsUsed:
                        match = False
                # numberOfInstruments
                numberOfInstruments = int(row[9])
                if numberOfInstruments != -1:
                    if sum(i for i in o for o in arch) != numberOfInstruments:
                        match = False
                # Append res if match == True
                features = ["present", "abscent", "inOrbit", "notInOrbit", "together", "togetherInOrbit", "Separate", "emptyOrbit", "numberOfOrbitsUsed", "numberOfInstruments"]
                if match == True:
                    res.append("&&".join([("%s(%s)" % (features[i] ,row[i])) \
                         for i in range(len(row)) if ( row[i] != '' and row[i] != "[\"\",\"\",\"\",\"\",\"\"]" and row[i] != "[\"\",-1]" and row[i] != "-1")]))
        return res

    def arch_differences(self, arch1, arch2):
        result = []
        aa = []
        bb = []
        N = max(len(arch1), len(arch2))
        a = arch1 + ['']*(N - len(arch1))
        b = arch2 + ['']*(N - len(arch2))
        for o in range(N):
            i = 0
            while True:
                if i == len(a[o]):
                    break
                if b[o].find(a[o][i]) != -1:
                    b[o] = b[o].replace(a[o][i],'',1)
                    a[o] = a[o].replace(a[o][i],'',1)
                else:
                    i += 1
            aa.append(a[o])
            bb.append(b[o])
        for o1 in range(N):
            for i1 in range(len(aa[o1])):
                match = False
                for o2 in range(N):
                    if bb[o2].find(aa[o1][i1]) != -1:
                        bb[o2] = bb[o2].replace(aa[o1][i1],'',1)
                        match = True
                        break
                if match == True:
                    result.append(["moved", o1, o2, aa[o1][i1]])
                else:
                    result.append(["deleted", o1, aa[o1][i1]])
        for o2 in range(N):
            for i2 in range(len(bb[o2])):
                result.append(["added", o2, bb[o2][i2]])
        return result

    def match_similar(self, arch):
        res = []
        with open("./iFEED_API/data/EOSS_data.csv", "r") as csvfile:
            architectures = csv.reader(csvfile, delimiter=',')
            for row in architectures:
                diff = self.arch_differences(arch, self.get_arnau_format(row[0]))
                # Get similar architectures (1 change maximum)
                if len(diff) == 1:
                    res.append([diff, float(row[1]), float(row[2])])
        return res

    def p(self, l):
        if not l: return [[]]
        return self.p(l[1:]) + [[l[0]] + x for x in self.p(l[1:])]


    def generate_critic1(self):
        out_filename = "CRITIC1.csv"
        f = open(out_filename, 'w')
        # For each instrument in each possible orbit (5*12=60)
        for orbit in self.orbits_dataset:
            for instrument in self.instruments_dataset:
                # Get similar instruments from the database
                result = self.get_similar_instruments(orbit, instrument)
                # Write results to the output file
                f.write(orbit["alias"]+"\t"+instrument["alias"]+"\t"+str(len(result))+"\t"+str([r.name for r in result])+"\n")
        f.close()


    def generate_critic2(self):
        out_filename = "CRITIC2.csv"
        f = open(out_filename, 'w')
        # Get missions in the database
        missionsDatabase = self.session.query(models.Mission)
        # For each combination of instruments in each possible orbit ((2^12)*5 = 20480)
        for orbit1 in self.orbits_dataset:
            for instruments1 in self.p(self.instruments_dataset):
                # Get similar missions from the database
                result = self.missions_similarity(orbit1, instruments1, missionsDatabase)
                # Write results to the output file
                if result["maxScore"] != -1:
                    f.write(orbit1["alias"]+"\t"+str(sorted([i["alias"] for i in instruments1]))+"\t"+result[1].name+"\t"+str(result[0])+"\n")
        f.close()


    def historian_critic(self, arch):
        result = []
        # Convert architecture format
        arch_critic = self.get_arnau_format(arch)

        # Type 2: Mission by mission
        missions_database = self.session.query(models.Mission)
        for o in range(len(arch_critic)):
            orbit = self.orbits_dataset[o]
            instruments = [next(ii for ii in self.instruments_dataset if ii["alias"] == i) for i in arch_critic[o]]
            res = self.missions_similarity(orbit, instruments, missions_database)
            if len(instruments) > 0:
                if res[0] < 6:
                    result.append("No past mission is similar to your satellite in orbit %s. Consider changing it." % \
                                  orbit["name"])
                else:
                    result.append("A past mission is really similar to your design in orbit %s: %s. You can probably focus on other orbits for now." % \
                                  (orbit["name"], res[1].name))
                        # +
                        # '<br>'.join(["Instrument similar to %s (score: %.2f)" % \
                        #    (i[0], i[2]) for i in self.instruments_match_dataset(res[1].instruments)]) + '.')
        return result

    def analyst_critic(self, arch):
        result = []
        # Convert architecture format
        arch_critic = self.get_arnau_format(arch)

        if len(''.join(arch_critic)) > 0:
            res = self.match_features(arch_critic)
            if len(res) == 0:
                result.append("Your design doesn't have much in common with other good designs.")
            else:
                result.append("Your design seems to have %d common features among good designs" % len(res) +
                    '<br>'.join(["Features: %s" % r for r in res]) + '.')
        return result


    def explorer_critic(self, arch):
        result = []
        # Convert architecture format
        arch_critic = self.get_arnau_format(arch)

        if len(''.join(arch_critic)) > 0:
            pass
            # TODO: Use the local search by Harris instead of the Arnau function
            # res = self.match_similar(arch_critic)
            # if len(res) == 0:
            #     result.append({
            #         "type": "Explorer",
            #         "advice": "I tried a few changes and couldn't find an easy way to improve your design."
            #     })
            # else:
            #     result.append({
            #         "type": "Explorer",
            #         "advice": "I have found %d designs that are similar to yours but a little better " % len(res) +
            #         '<br>'.join(["Designs: %s (Science: %.2f, Cost: %.2f)" % (r[0], r[1], r[2]) for r in res]) + '.'
            #     })
        return result

    def criticize_arch(self, arch):
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
        historian_results = self.historian_critic(arch)
        for hist in historian_results:
            result.append({
                "type": "Historian",
                "advice": hist
            })

#        # Analyst
#        analyst_results = self.analyst_critic(arch)
#        for anal in analyst_results:
#            result.append({
#                "type": "Analyst",
#                "advice": anal
#            })

#        # Explorer
#        explorer_results = self.explorer_critic(arch)
#        for expl in explorer_results:
#            result.append({
#                "type": "Explorer",
#                "advice": expl
#            })

        # Return result
        return result
