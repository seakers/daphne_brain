(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::find-list-of-low-TRL-instruments
    (declare (salience 100))
    ?ltrl <- (CRITIQUE-PERFORMANCE-PARAM::list-of-low-TRL-instruments (list $?l))
    (DATABASE::Instrument (Name ?instr&:(not-contains$ ?instr $?l)) (Technology-Readiness-Level ?trl&: (< ?trl 5)))
    =>
    (modify ?ltrl (list $?l ?instr)))


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::get-number-of-low-TRL-instrument
    (declare (salience 90))
    ?miss <- (MANIFEST::Mission (Name ?n) (low-TRL-instruments# nil) (instruments $?instr-list))
    (CRITIQUE-PERFORMANCE-PARAM::list-of-low-TRL-instruments (list $?l))
    =>
    (bind ?c 0)
    (bind ?i 1)
    (while (< ?i (+ (length$ $?l) 1)) do
        (if (numberp (member$ (nth$ ?i $?l) ?instr-list))
        then (bind ?c (+ ?c 1)) else )
        (bind ?i (+ ?i 1))
    )
    (modify ?miss (low-TRL-instruments# ?c)))


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::find-lowest-TRL-instrument-for-each-satellite
    (declare (salience 100))
    ?miss <- (MANIFEST::Mission (Name ?n) (instruments $?instr-list) (lowest-TRL-instrument-value# ?lowest-trl))
    (DATABASE::Instrument (Name ?instr&:(numberp (member$ ?instr $?instr-list))) (Technology-Readiness-Level ?trl))
    =>
    (if (eq ?lowest-trl nil)
    then (modify ?miss (lowest-TRL-instrument-value# ?trl))
    else (if (< ?trl ?lowest-trl)
        then (modify ?miss (lowest-TRL-instrument-value# ?trl))))
)


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::predict-launch-date-based-on-lowest-TRL-instrument
    (declare (salience 90))
    ?miss <- (MANIFEST::Mission (Name ?n) (lowest-TRL-instrument-value# ?lowest-trl) (instruments $?instr-list))
    =>
    (bind ?instr-num (length$ $?instr-list))
    (if (= ?lowest-trl 3) then (bind ?ld 15))
    (if (= ?lowest-trl 4) then (bind ?ld 10))
    (if (= ?lowest-trl 5) then (bind ?ld 7))
    (if (= ?lowest-trl 6) then (bind ?ld 5))
    (if (= ?lowest-trl 7) then (bind ?ld 3))
    (if (= ?lowest-trl 8) then (bind ?ld 2))
    (if (= ?lowest-trl 9) then (bind ?ld 1))
    (assert (CRITIQUE-PERFORMANCE-PARAM::launch-delay-metric (name ?n) (weight ?instr-num) (launch-date ?ld)))
)


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::launch-delay-metric-calculation
    (declare (salience 80))
    ?c <- (CRITIQUE-PERFORMANCE-PARAM::launch-delay-metric-cumulative (orbits-considered $?o)(value ?v))
    (CRITIQUE-PERFORMANCE-PARAM::launch-delay-metric (name ?n&:(not (numberp (member$ ?n $?o))))(weight ?w) (launch-date ?ld))
    =>
    (bind ?new-v (* 1000 (+ ?v (* ?w (exp (- 0 ?ld))))))
    (modify ?c (value ?new-v) (orbits-considered $?o ?n))
)


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::number-of-instruments
    (declare (salience 100))
    ?miss <- (MANIFEST::Mission (num-of-instruments# nil)(instruments $?instr))
    ?ninstr <- (CRITIQUE-PERFORMANCE-PARAM::total-num-of-instruments (value ?v))
    =>
    (bind ?c (length$ $?instr))
    (modify ?miss (num-of-instruments# ?c))
    (modify ?ninstr (value (+ ?v ?c))))


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::copy-datarate-duty-cycle
"Copies datarate duty-cycle information from CAPABILITIES module to MANIFEST::Mission"
    (declare (salience 100))
    (CAPABILITIES::can-measure (instrument ?ins) (in-orbit ?n) (can-take-measurements yes) (data-rate-duty-cycle# ?dc&~nil))
    ?miss <- (MANIFEST::Mission (Name ?n) (datarate-duty-cycle# nil))
    =>
    (modify ?miss (datarate-duty-cycle# ?dc))
)


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::copy-power-duty-cycle 
"Copies power duty-cycle information from CAPABILITIES module to MANIFEST::Mission"
    (declare (salience 100))
    (CAPABILITIES::can-measure (instrument ?ins) (in-orbit ?n) (can-take-measurements yes) (power-duty-cycle# ?dc&~nil))
    ?miss <- (MANIFEST::Mission (Name ?n) (power-duty-cycle# nil))
    =>
    (modify ?miss (power-duty-cycle# ?dc)))


(defrule CRITIQUE-PERFORMANCE-PRECALCULATION::fairness-check
    (declare (salience 100))
    (AGGREGATION::STAKEHOLDER (id ?id1) (satisfaction ?s1))
    (AGGREGATION::STAKEHOLDER (id ?id2&~id1) (satisfaction ?s2))
    ?f <- (CRITIQUE-PERFORMANCE-PARAM::fairness (stake-holder1 nil) (stake-holder2 nil)(value nil) (flag 0))
    =>
    (if (> (- ?s1 ?s2) 0.3)
    then (modify ?f  (flag 1)(value (- ?s1 ?s2)) (stake-holder1 ?id1) (stake-holder2 ?id2)))
    (if (> (- ?s2 ?s1) 0.3)
    then (modify ?f (flag 1)(value (- ?s2 ?s1)) (stake-holder1 ?id2) (stake-holder2 ?id1)))
    )