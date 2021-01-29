(defrule SEARCH-HEURISTICS::improve-orbit
    "This heuristic moves a random instrument to a better orbit" 
    ?arch0 <- (MANIFEST::ARCHITECTURE (bitString ?orig) (num-sats-per-plane ?ns) (improve improveOrbit) (factHistory ?fh))
    =>
	;(printout t improve-orbit crlf)
    (bind ?N 1)
    (for (bind ?i 0) (< ?i ?N) (++ ?i) 
		(bind ?arch ((new seakers.vassar.Architecture ?orig ?ns) improveOrbit))
    	(assert-string (?arch toFactString)))
	(modify ?arch0 (improve no) (factHistory (str-cat "{R" (?*rulesMap* get SEARCH-HEURISTICS::improve-orbit) " " ?fh "}")))
    )

; this deffacts is moved to JessInitializer.java	
;(deffacts DATABASE::add-improve-orbit-list-of-improve-heuristics
;(SEARCH-HEURISTICS::improve-heuristic (id improveOrbit))
;)

