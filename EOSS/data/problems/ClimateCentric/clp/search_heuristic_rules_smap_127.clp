(defrule DATABASE::create-list-of-improve-heuristics
	?ret <- (SEARCH-HEURISTICS::improve-heuristic (id ?id))
	?f <- (SEARCH-HEURISTICS::list-improve-heuristics (list $?list) (num-heuristics ?n))
	=>
	(bind ?new-list (append$ $?list ?id))
	(modify ?f (list ?new-list) (num-heuristics (+ ?n 1)))
	(retract ?ret)
)
(defrule SEARCH-HEURISTICS::mutation-swap-one-bit 
    "This mutation function swaps the value of a single bit" 
	(declare (salience 100))
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (mutate yes))
    =>
	;(printout t mutation-swap-one-bit crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i)
	    
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) mutate1bit))
    	(assert-string (?arch toFactString)))
	(retract ?arch0)
    )
(deffacts DATABASE::assert-empty-list-of-improve-heuristics
(SEARCH-HEURISTICS::list-improve-heuristics (list (create$ )) (num-heuristics 0))
)


	 
(defrule SEARCH-HEURISTICS::crossover-one-point
    "This mutation performs crossover on one point" 
    ?arch1 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (heuristics-to-apply $? crossover1point $?) (heuristics-applied $?applied&:(not-contains$ crossover1point $?applied)))
	?arch2 <- (MANIFEST::ARCHITECTURE (bitString ?orig2&~?orig)(num-sats-per-plane ?ns2) (heuristics-to-apply $? crossover1point $?) (heuristics-applied $?applied&:(not-contains$ crossover1point $?applied)))
    => 
	;(printout t crossover-one-point crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i)   
		(bind ?arch3 ((new seakers.vassar.Architecture ?orig ?ns) crossover1point (new seakers.vassar.Architecture ?orig2 ?ns2)))
    	(assert-string (?arch3 toFactString))
		(bind ?arch4 ((new seakers.vassar.Architecture ?orig2 ?ns2) crossover1point (new seakers.vassar.Architecture ?orig ?ns)))
    	(assert-string (?arch4 toFactString))
		)
	(modify ?arch1 (heuristics-applied (append$ ?applied crossover1point)))
	(modify ?arch2 (heuristics-applied (append$ ?applied crossover1point)))
    ) 
	
(deffacts DATABASE::add-crossover-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id crossover1point))
)

(defrule SEARCH-HEURISTICS::improve-orbit
    "This heuristic moves a random instrument to a better orbit" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (heuristics-to-apply $? improveOrbit $?) (heuristics-applied $?applied&:(not-contains$ improveOrbit $?applied)))
    =>
	;(printout t improve-orbit crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) improveOrbit))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (heuristics-applied (append$ ?applied improveOrbit)))
    )
	 
(deffacts DATABASE::add-improve-orbit-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id improveOrbit))
)

(defrule SEARCH-HEURISTICS::remove-existing-interference
    "This heuristic finds an existing interference between instruments and removes the necessary instrument" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (improve removeInterference))
    =>
	;(printout t remove-existing-interference crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) removeInterference))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (improve no))
    )
	 
(deffacts DATABASE::add-remove-interf-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id removeInterference))
)

(defrule SEARCH-HEURISTICS::complete-missing-synergies
    "This heuristic finds a missing synergy and adds the necessary instrument" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (heuristics-to-apply $? addSynergy $?) (heuristics-applied $?applied&:(not-contains$ addSynergy $?applied)))
    =>
	;(printout t complete-missing-synergies crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) addSynergy))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (heuristics-applied (append$ ?applied addSynergy))))
    
	
	(deffacts DATABASE::add-missing-synergies-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id addSynergy))
)

(defrule SEARCH-HEURISTICS::remove-superfluous-instrument
    "This heuristic finds an existing superfluous instruments and removes it" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (heuristics-to-apply $? removeSuperfluous $?) (heuristics-applied $?applied&:(not-contains$ removeSuperfluous $?applied)))
    =>
	;(printout t remove-existing-interference crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) removeSuperfluous))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (heuristics-applied (append$ ?applied removeSuperfluous)))
    )
	 
(deffacts DATABASE::add-remove-superfluous-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id removeSuperfluous))
)

(defrule SEARCH-HEURISTICS::add-random-instrument-to-small-sat
    "This heuristic finds an existing small satellite and adds a random instrument" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (heuristics-to-apply $? addRandomToSmallSat $?) (heuristics-applied $?applied&:(not-contains$ addRandomToSmallSat $?applied)))
    =>
	;(printout t add-random-instrument-to-small-sat crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) addRandomToSmallSat))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (heuristics-applied (append$ ?applied addRandomToSmallSat)))
    )
	 
(deffacts DATABASE::add-random-instrument-to-small-sat-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id addRandomToSmallSat))
)

(defrule SEARCH-HEURISTICS::remove-random-instrument-from-loaded-sat
    "This heuristic removes a random instrument from an existing loaded satellite" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns)(heuristics-to-apply $? removeRandomFromLoadedSat $?) (heuristics-applied $?applied&:(not-contains$ removeRandomFromLoadedSat $?applied)))
    =>
	;(printout t remove-existing-interference crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) removeRandomFromLoadedSat))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (heuristics-applied (append$ ?applied removeRandomFromLoadedSat)))
    )
	 
(deffacts DATABASE::add-remove-random-instrument-from-loaded-sat-list-of-improve-heuristics
(SEARCH-HEURISTICS::improve-heuristic (id removeRandomFromLoadedSat))
)

