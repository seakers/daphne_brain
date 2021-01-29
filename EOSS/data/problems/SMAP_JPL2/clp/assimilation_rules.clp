;; assimilation_rules.clp
;(defrule ASSIMILATION::test 
;    (declare (salience 5))
;    ?c <- (accumulate (bind ?map (new java.util.HashMap))   ;; initializer
;                ((lambda (?pa ?alt ?ra ?an ?fo ?in) 
;                (if (?map containsKey ?pa) then 
;                    (bind ?x (?map get ?pa)) 
;                    (?x add (create$ ?fo ?alt ?in ?ra ?an)) 
;                    (?map put ?pa ?x) 
 ;                else 
 ;               	(bind ?list (new java.util.ArrayList))  
 ;                   (?list add (create$ ?fo ?alt ?in ?ra ?an))
 ;                   (?map put ?pa ?list)
 ;                ))
 ;            ?p ?h ?raan ?ano ?fov ?inc)
 ;                ?map                                        ;; result
 ;               (REQUIREMENTS::Measurement (Parameter ?p&~nil) (Field-of-view# ?fov) (orbit-inclination ?inc) (orbit-RAAN ?raan) (orbit-altitude# ?h) (orbit-anomaly# ?ano) (Id ?id)
 ;                         ))  ;; CE
 ;   =>
 ;   (store MAP ?c)
 ;   ;(printout t (?c toString) crlf)
 ;   )

;(defrule ASSIMILATION::test  
;    (declare (salience 5)) 
;     ?c <- (accumulate 
;        (bind ?map (new java.util.HashMap))  
;        ((lambda (?pa ?alt ?ra ?an ?fo ?in)  
;                (if (?map containsKey ?pa) then  
;                    (bind ?x (?map get ?pa))  
;                    (?x add (create$ ?fo ?alt ?in ?ra ?an))  
;                    (?map put ?pa ?x)  else 	
;                    (bind ?list (new java.util.ArrayList))     
;                    (?list add (create$ ?fo ?alt ?in ?ra ?an))  ;
;					(?map put ?pa ?list)  ))  ?p ?h ?raan ?ano ?fov ?inc)  
;         ?map
;           (REQUIREMENTS::Measurement (Parameter ?p&~nil) (Field-of-view# ?fov) (orbit-inclination ?inc) (orbit-RAAN ?raan) (orbit-altitude# ?h) (orbit-anomaly# ?ano) (Id ?id)       ))  ;; CE 
;     =>  
;    (store MAP ?c)  )
    
;(defrule ASSIMILATION::compute-temporal-resolution#-from-revisit-times
;    (declare (salience -5))
;    ?meas <- (REQUIREMENTS::Measurement (Region-of-interest ?region) (Temporal-resolution nil) (Temporal-resolution# nil) (avg-revisit-time-global# ?revtime-global&~nil) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH) (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US))
;    =>
;    (bind ?tr (revisit-time-to-temporal-resolution ?region (create$ ?revtime-global ?revtime-tropics ?revtime-NH ?revtime-SH ?revtime-cold ?revtime-US)))
;    (modify ?meas (Temporal-resolution# ?tr))
;    )

(deffunction adapt-GEO-revisit (?tr)
	(return (+ ?tr 0.01))
	)
(defrule ASSIMILATION2::modify-temporal-resolution
	?sub <-(ASSIMILATION2::UPDATE-REV-TIME (parameter ?p) (avg-revisit-time-global# ?new-time)
	(avg-revisit-time-US# ?new-time-us))
	?meas <- (REQUIREMENTS::Measurement (Parameter ?p) (Temporal-resolution# nil) (Temporal-resolution nil) (Coverage ?region)(factHistory ?fh))
	=>
	(if (eq ?region Global) then (bind ?tr ?new-time) else (bind ?tr ?new-time-us))
	(modify ?meas (Temporal-resolution# ?tr) (avg-revisit-time-global# ?new-time) (avg-revisit-time-US# (adapt-GEO-revisit ?new-time-us))(factHistory (str-cat "{R" (?*rulesMap* get ASSIMILATION2::modify-temporal-resolution) " " ?fh " S" (call ?sub getFactId) "}"))) 
)

;(defrule ASSIMILATION::compute-temporal-resolution#-from-revisit-times
;    ?meas <- (REQUIREMENTS::Measurement (Coverage ?region) (Temporal-resolution nil) (Temporal-resolution# nil)
;         (avg-revisit-time-global# ?revtime-global&~nil) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH)
;         (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US))
;    =>
;    (bind ?tr (revisit-time-to-temporal-resolution ?region (create$ ?revtime-global ?revtime-tropics ?revtime-NH ?revtime-SH ?revtime-cold ?revtime-US)))
;    ;(printout t "tr = "?tr crlf)
;    (modify ?meas (Temporal-resolution# ?tr))
;    )

(defrule CAPABILITIES::global-or-regional-coverage
	?meas <- (REQUIREMENTS::Measurement (Coverage nil) (orbit-type ?orb &~nil) (factHistory ?fh))
	=>
	(if (eq ?orb GEO) then (bind ?coverage US) else (bind ?coverage Global))
	(modify ?meas (Coverage ?coverage) (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::global-or-regional-coverage) " " ?fh "}")))
	)
	

;(defrule ASSIMILATION::compute-global-temporal-resolution#-from-revisit-time
;    ?meas <- (REQUIREMENTS::Measurement (Temporal-resolution nil) (Temporal-resolution# nil)
;         (avg-revisit-time-global# ?revtime-global&~nil))
;    =>
;    
;    (duplicate ?meas (Coverage Global) (Temporal-resolution# ?revtime-global))
;    )

	
;(defrule ASSIMILATION::compute-US-temporal-resolution#-from-revisit-time
;    ?meas <- (REQUIREMENTS::Measurement  (Temporal-resolution nil) (Temporal-resolution# nil)
;         (avg-revisit-time-US# ?revtime&~nil))
;    =>
;    
;    (duplicate ?meas (Coverage US) (Temporal-resolution# ?revtime))
;    )
	