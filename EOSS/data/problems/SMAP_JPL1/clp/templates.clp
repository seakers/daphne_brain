(deftemplate SYNERGIES::NUM-CHANNELS (slot num-channels) (slot factHistory))

(deftemplate DATABASE::Revisit-time-of "Revisit time of an architecture-orbit-instrument tuple" 
   (slot mission-architecture) 
   (slot num-of-planes#)  
   (slot num-of-sats-per-plane#)  
   (slot orbit-altitude#) 
   (slot orbit-type) 
   (slot orbit-inclination) 
   (slot orbit-raan) 
   (slot instrument-field-of-view#) 
   (slot avg-revisit-time-global#) 
   (slot avg-revisit-time-tropics#) 
   (slot avg-revisit-time-northern-hemisphere#) 
   (slot avg-revisit-time-southern-hemisphere#) 
   (slot avg-revisit-time-cold-regions#) 
   (slot avg-revisit-time-US#)
   (slot factHistory)   
   )
(deftemplate SEARCH-HEURISTICS::improve-heuristic (slot id)(slot factHistory))

(deftemplate SEARCH-HEURISTICS::list-improve-heuristics (multislot list) (slot num-heuristics (default 0))(slot factHistory))
(deftemplate SYNERGIES::cross-registered "Declare a set of measurements as cross-registered"
    (multislot measurements) (slot degree-of-cross-registration) (slot platform)(slot factHistory))
  
(deftemplate SYNERGIES::cross-registered-instruments "Declare a set of measurements as cross-registered"
    (multislot instruments) (slot degree-of-cross-registration) (slot platform)(slot factHistory))

(deftemplate REASONING::partially-satisfied "Requirements that are partially satisfied" (slot subobjective)
    (slot objective) (slot parameter) (slot taken-by) (slot attribute) (slot required) (slot achieved)(slot factHistory))

(deftemplate REASONING::fully-satisfied "Requirements that are partially satisfied" (slot subobjective)
    (slot objective) (slot parameter) (slot taken-by)(slot factHistory))
(deftemplate REASONING::stop-improving "Flag to stop improving a measurement through application of synergy rules" (slot Measurement)(slot factHistory))

(deftemplate REASONING::architecture-eliminated "Reasons why architecture was eliminated" (slot arch-id) (slot fit) (slot arch-str) 
(slot benefit) (slot lifecycle-cost) (slot utility) (slot pareto-ranking) (slot programmatic-risk) (slot fairness) (slot launch-risk) (slot reason-id) 
(slot data-continuity) (slot discounted-value) (slot reason-str)(slot factHistory))
	
(deftemplate ASSIMILATION2::UPDATE-REV-TIME (slot parameter ) (slot avg-revisit-time-global#) (slot avg-revisit-time-US#)(slot factHistory))

(deftemplate AGGREGATION::STAKEHOLDER (slot id) (slot fuzzy-value) (slot parent) (slot index) (slot satisfaction) (slot satisfied-by) (multislot obj-fuzzy-scores) (multislot obj-scores) (slot reason) (multislot weights)(slot factHistory))
(deftemplate AGGREGATION::OBJECTIVE (slot id) (slot fuzzy-value) (slot index) (slot satisfaction) (slot reason) (multislot subobj-fuzzy-scores) (multislot subobj-scores) (slot satisfied-by) (slot parent) (multislot weights)(slot factHistory))
(deftemplate AGGREGATION::SUBOBJECTIVE (slot id) (slot fuzzy-value) (slot index) (slot satisfaction) (multislot attributes) (multislot attrib-scores) (multislot reasons) (slot reason) (slot satisfied-by) (slot parent) (slot requirement-id) (slot factHistory))
(deftemplate AGGREGATION::ATTRIBUTE (slot id) (slot fuzzy-value) (slot satisfaction) (slot reason) (slot satisfied-by) (slot parent)(slot factHistory))
(deftemplate AGGREGATION::VALUE (slot satisfaction) (slot fuzzy-value) (slot reason) (multislot weights) (multislot sh-scores) (multislot sh-fuzzy-scores)(slot factHistory))

(deftemplate REASONING::fuzzy-number (slot value) (slot value#) (slot type) (slot id) (multislot interval) (slot unit) (slot explanation)(slot factHistory))

	
(deftemplate ORBIT-SELECTION::orbit (slot orb) (slot of-instrument) (slot in-mission) (slot is-type) (slot h) (slot i) (slot e) (slot a) (slot raan) (slot anomaly) (slot penalty-var)(slot factHistory) )
(deftemplate ORBIT-SELECTION::launcher (slot lv) (multislot performance) (slot cost) (slot diameter) (slot height)(slot factHistory) )
	
(deftemplate CAPABILITIES::can-measure (slot instrument) (slot in-orbit) (slot orbit-type) (slot orbit-altitude#) (slot data-rate-duty-cycle#) (slot power-duty-cycle#) (slot data-rate-constraint) (slot orbit-inclination) (slot orbit-RAAN) (slot can-take-measurements) (slot reason)(slot copied-to-measurement-fact)(slot factHistory))
(deftemplate CAPABILITIES::resource-limitations (slot mission) (multislot instruments) (slot data-rate-duty-cycle#) (slot power-duty-cycle#) (slot reason)(slot factHistory))
(deftemplate DOWN-SELECTION::MAX-COST (slot max-cost) (slot factHistory))	
(deftemplate DOWN-SELECTION::MIN-SCIENCE (slot min-benefit)(slot factHistory))
(deftemplate DOWN-SELECTION::MIN-PARETO-RANK (slot min-pareto-rank)(slot factHistory))
(deftemplate DOWN-SELECTION::MIN-UTILITY (slot min-utility)(slot factHistory))

(deftemplate CRITIQUE-PERFORMANCE-PARAM::total-num-of-instruments (slot value))
(deftemplate CRITIQUE-PERFORMANCE-PARAM::list-of-low-TRL-instruments (multislot list))
(deftemplate CRITIQUE-PERFORMANCE-PARAM::list-of-active-instruments (multislot list))
(deftemplate CRITIQUE-PERFORMANCE-PARAM::fairness (slot stake-holder1) (slot stake-holder2)(slot value) (slot flag))
(deftemplate CRITIQUE-PERFORMANCE-PARAM::launch-delay-metric (slot name) (slot weight) (slot launch-date))
(deftemplate CRITIQUE-PERFORMANCE-PARAM::launch-delay-metric-cumulative (multislot orbits-considered)(slot value))
(deftemplate CRITIQUE-COST-PARAM::satellite-max-size-ratio (slot value) (slot big-name) (slot small-name) )
(deftemplate CRITIQUE-COST-PARAM::satellite-max-cost-ratio (slot value) (slot big-name) (slot small-name))
(deftemplate CRITIQUE-COST-PARAM::launch-packaging-factors (slot name) (slot performance-mass-ratio) (slot diameter-ratio) (slot height-ratio))
(deftemplate CRITIQUE-COST-PARAM::launch-packaging-factors-temp (slot name) (slot performance) (slot mass) (slot diameter-lv) (slot diameter) (slot height-lv) (slot height) (multislot dimensions))