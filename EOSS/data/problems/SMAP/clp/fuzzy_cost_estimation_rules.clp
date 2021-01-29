; ********************
; Payload cost (salience 20)
; ********************

(deffunction is-domestic (?who)
    (return (eq (sub-string 1 3 ?who) "DOM"))
    )

(deffunction sum$ (?list)
    (if (eq (length$ ?list) 1) then (return (nth$ 1 ?list))
        else (return (+ (nth$ 1 ?list) (sum$ (rest$ ?list)))))
    )


(deffunction apply-NICM (?m ?p ?rb)
    
    (bind ?cost (* 25600 (** (/ ?p 61.5) 0.32) (** (/ ?m 53.8) 0.26) 
            (** (/ (* 1000 ?rb) 40.4) 0.11))); in FY04$
    (bind ?cost (/ ?cost 1.097))
    ;(printout t apply-NICM " " ?instr " = " ?m " " ?p " " ?rb " " ?cost crlf)
    (return ?cost)
    )
	
;(deffunction apply-NICM (?instr)
;    (bind ?m (get-instrument-mass ?instr))
;    (bind ?p (get-instrument-power ?instr))
;    (bind ?rb (get-instrument-datarate ?instr))
;    
;    (bind ?cost (* 25600 (** (/ ?p 61.5) 0.32) (** (/ ?m 53.8) 0.26) 
;            (** (/ (* 1000 ?rb) 40.4) 0.11))); in FY04$
;    (bind ?cost (/ ?cost 1.097))
;    ;(printout t apply-NICM " " ?instr " = " ?m " " ?p " " ?rb " " ?cost crlf)
;    (return ?cost)
;    )

;(defrule FUZZY-COST-ESTIMATION::estimate-instrument-cost
;    "This rule estimates payload cost using a very simplified version of the 
;    NASA Instrument Cost Model available on-line"
;    (declare (salience 25) (no-loop TRUE))
;    ?instr <- (DATABASE::Instrument (cost# nil) (Name ?name) 
;        (developed-by ?whom)
;        )
;    =>  
;    (bind ?c0 (apply-NICM ?name)) 
;    (if (is-domestic ?whom) then (modify ?instr (cost (cost-fv ?c0 39.0)) (cost# ?c0)) 
;        else (modify ?instr (cost# 0) (cost (cost-fv 0 0))))
;    )

(defrule FUZZY-COST-ESTIMATION::estimate-instrument-cost
    "This rule estimates payload cost using a very simplified version of the 
    NASA Instrument Cost Model available on-line"
    (declare (salience 25) (no-loop TRUE))
    ?instr <- (CAPABILITIES::Manifested-instrument (cost# nil) (mass# ?m&~nil) (average-power# ?p&~nil) (average-data-rate# ?rb&~nil)
        (developed-by ?whom) (factHistory ?fh))
    =>  
    (bind ?c0 (apply-NICM ?m ?p ?rb)) 
    (if (is-domestic ?whom) then (modify ?instr (cost (cost-fv ?c0 39.0)) (cost# ?c0) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-instrument-cost) " " ?fh "}"))) 
        else (modify ?instr (cost# 0) (cost (cost-fv 0 0)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-instrument-cost) " " ?fh "}"))))
    )

(defrule FUZZY-COST-ESTIMATION::estimate-payload-cost2
    "This rule estimates payload cost using a very simplified version of the 
    NASA Instrument Cost Model available on-line"
    (declare (salience 18))
    ?miss <- (MANIFEST::Mission (payload-cost# nil) (instruments $?payload) (factHistory ?fh)
        )
    =>
    (bind ?costs (map get-instrument-cost-manifest ?payload)); in FY04$
    (bind ?fuzzy-costs (map get-instrument-fuzzy-cost-manifest ?payload)); in FY04$
    ;(printout t "estimate payload cost: instrument costs = " ?costs crlf)
    (bind ?cost (sum$ ?costs)); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
    (bind ?fuzzy-cost (fuzzysum$ ?fuzzy-costs)); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
        (modify ?miss (payload-cost# ?cost) (payload-non-recurring-cost# (* 0.8 ?cost))
        (payload-recurring-cost# (* 0.2 ?cost))
        (payload-cost ?fuzzy-cost) (payload-non-recurring-cost (fuzzyscprod ?fuzzy-cost 0.8))
        (payload-recurring-cost (fuzzyscprod ?fuzzy-cost 0.2)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-payload-cost2) " " ?fh "}")))
    )

; ********************
; Bus cost (salience 10)
; ********************

; bus non recurring cost
(defrule FUZZY-COST-ESTIMATION::estimate-bus-non-recurring-cost
    "This rule estimates bus non-recurring cost using SMAD CERs"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (bus-non-recurring-cost# nil) 
        (satellite-BOL-power# ?p&~nil) (EPS-mass# ?epsm&~nil) (thermal-mass# ?thm&~nil)
        (structure-mass# ?strm &~nil) (propulsion-mass# ?prm&~nil) (avionics-mass# ?comm&~nil)
        (ADCS-mass# ?adcm&~nil) (standard-bus ?bus) (factHistory ?fh)
        )
    (or (test (eq ?bus nil)) (test (eq ?bus dedicated-class)))
    =>
    (bind ?str-cost (* 157 (** ?strm 0.83))) 
    (bind ?prop-cost (* 17.8 (** ?prm 0.75)))
    (bind ?adcs-cost (* 464 (** ?adcm 0.867)))
    (bind ?comm-cost (* 545 (** ?comm 0.761)))
    (bind ?therm-cost (* 394 (** ?thm 0.635)))
    (bind ?pow-cost (* 2.63 (** (* ?epsm ?p) 0.712)))
    
    (bind ?fz-str-cost (cost-fv ?str-cost 40)) 
    (bind ?fz-prop-cost (cost-fv ?prop-cost 30))
    (bind ?fz-adcs-cost (cost-fv ?adcs-cost 35))
    (bind ?fz-comm-cost (cost-fv ?comm-cost 30))
    (bind ?fz-therm-cost (cost-fv ?therm-cost 35))
    (bind ?fz-pow-cost (cost-fv ?pow-cost 40))
    
    (bind ?cost (+ ?str-cost ?prop-cost ?adcs-cost ?comm-cost ?therm-cost ?pow-cost)); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
    (bind ?fuzzy-cost (fuzzysum$ (create$ ?fz-str-cost 
                ?fz-prop-cost ?fz-adcs-cost ?fz-comm-cost ?fz-therm-cost 
                ?fz-pow-cost))); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
    (modify ?miss (bus-non-recurring-cost ?fuzzy-cost)  
            (bus-non-recurring-cost# ?cost) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-bus-non-recurring-cost) " " ?fh "}")))
    )

; bus recurring cost
(defrule FUZZY-COST-ESTIMATION::estimate-bus-TFU-recurring-cost
    "This rule estimates bus recurring cost (TFU) using SMAD CERs"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (bus-recurring-cost# nil) 
        (EPS-mass# ?epsm&~nil) (thermal-mass# ?thm&~nil) (avionics-mass# ?comm&~nil)
        (structure-mass# ?strm &~nil) (propulsion-mass# ?prm&~nil) 
        (ADCS-mass# ?adcm&~nil) (standard-bus ?bus) (factHistory ?fh)
        )
    (or (test (eq ?bus nil)) (test (eq ?bus dedicated-class)))
    =>
    (bind ?str-cost (* 13.1 ?strm))
    (bind ?prop-cost (* 4.97 (** ?prm 0.823)))
    (bind ?adcs-cost (* 293 (** ?adcm 0.777)))
    (bind ?comm-cost (* 635 (** ?comm 0.568)))
    (bind ?therm-cost (* 50.6 (** ?thm 0.707)))
    (bind ?pow-cost (* 112 (** ?epsm 0.763)))
     (bind ?fz-str-cost (cost-fv ?str-cost 40)) 
    (bind ?fz-prop-cost (cost-fv ?prop-cost 30))
    (bind ?fz-adcs-cost (cost-fv ?adcs-cost 35))
    (bind ?fz-comm-cost (cost-fv ?comm-cost 30))
    (bind ?fz-therm-cost (cost-fv ?therm-cost 35))
    (bind ?fz-pow-cost (cost-fv ?pow-cost 40))
    
    (bind ?cost (+ ?str-cost ?prop-cost ?adcs-cost 
                ?comm-cost ?therm-cost ?pow-cost)); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
    (bind ?fuzzy-cost 
            (fuzzysum$ 
                (create$ ?fz-str-cost ?fz-prop-cost 
                    ?fz-adcs-cost ?fz-comm-cost ?fz-therm-cost 
                ?fz-pow-cost))); correct for inflation from FY04 to FY00, from http://oregonstate.edu/cla/polisci/faculty-research/sahr/cv2000.pdf
    (modify ?miss (bus-recurring-cost ?fuzzy-cost)  (bus-recurring-cost# ?cost) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-bus-TFU-recurring-cost) " " ?fh "}")))
        
    )

; ********************
; Total spacecraft cost (salience 5)
; ********************

; spacecraft recurring and non-recurring s/c cost
(defrule FUZZY-COST-ESTIMATION::estimate-spacecraft-cost-dedicated
    "This rule estimates s/c non recurring cost adding up bus and payload n/r cost"
    (declare (salience 5))
    ?miss <- (MANIFEST::Mission (spacecraft-non-recurring-cost# nil) (spacecraft-recurring-cost# nil)
        (bus-non-recurring-cost# ?busnr&~nil) (bus-recurring-cost# ?bus&~nil) (payload-cost# ?payl&~nil) (standard-bus ?sbus)
        (bus-non-recurring-cost ?fz-busnr&~nil) (bus-recurring-cost ?fz-bus&~nil) (payload-cost ?fz-payl&~nil) (factHistory ?fh))
    (or (test (eq ?sbus nil)) (test (eq ?sbus dedicated-class)))
    =>
    (bind ?spacecraftnr (+ ?busnr (* ?payl 0.6)))
    (bind ?spacecraft (+ ?bus (* ?payl 0.4)))
    (bind ?sat (+ ?spacecraftnr ?spacecraft))
    
    (bind ?fz-spacecraftnr (fuzzysum ?fz-busnr (fuzzyscprod ?fz-payl 0.6)))
    (bind ?fz-spacecraft (fuzzysum ?fz-bus (fuzzyscprod ?fz-payl 0.4)))
    (bind ?fz-sat (fuzzysum ?fz-spacecraftnr ?fz-spacecraft))
    (modify ?miss (spacecraft-non-recurring-cost# ?spacecraftnr) (spacecraft-non-recurring-cost ?fz-spacecraftnr)
         (spacecraft-recurring-cost# ?spacecraft) (bus-cost# (+ ?busnr ?bus))
                (spacecraft-recurring-cost ?fz-spacecraft) (bus-cost (fuzzysum ?fz-busnr ?fz-bus)) 
                (satellite-cost ?fz-sat) (satellite-cost# ?sat) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-spacecraft-cost-dedicated) " " ?fh "}")))
    )


; ********************
; Integration, assembly and testing cost (salience 0)
; ********************

; IA&T cost
(defrule FUZZY-COST-ESTIMATION::estimate-integration-and-testing-cost
    "This rule estimates Integration, assembly and testing non recurring and cost using SMAD CERs"
    ?miss <- (MANIFEST::Mission (IAT-non-recurring-cost# nil) (IAT-recurring-cost# nil) (IAT-cost# nil) 
        (spacecraft-non-recurring-cost# ?scnr&~nil) (satellite-dry-mass ?m&~nil) (factHistory ?fh)
        )
    =>
    (bind ?iatnr (+ 989 (* ?scnr 0.215)))
    (bind ?iatr (* 10.4 ?m))
    (bind ?iat (+ ?iatr ?iatnr))
    
    (bind ?fz-iatnr (cost-fv ?iatnr 30))
    (bind ?fz-iatr (cost-fv ?iatr 30))
    (bind ?fz-iat (fuzzysum ?fz-iatr ?fz-iatnr))
    
    (modify ?miss (IAT-non-recurring-cost# ?iatnr) (IAT-non-recurring-cost ?fz-iatnr)
         (IAT-recurring-cost ?fz-iatr) (IAT-cost ?fz-iat) (IAT-recurring-cost# ?iatr) (IAT-cost# ?iat) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-integration-and-testing-cost) " " ?fh "}")))
    )


; ********************
; Program overhead cost (salience 0)
; ********************
(defrule FUZZY-COST-ESTIMATION::estimate-program-overhead-cost
    "This rule estimates program overhead non recurring and cost using SMAD CERs"
    ?miss <- (MANIFEST::Mission (program-non-recurring-cost# nil) (program-recurring-cost# nil) (program-cost# nil) 
        (spacecraft-non-recurring-cost# ?scnr&~nil) (spacecraft-recurring-cost# ?scr&~nil) (factHistory ?fh)
        )
    =>
    (bind ?prognr (* 1.963 (** ?scnr 0.841)))
    (bind ?progr (* 0.341 ?scr))
    (bind ?prog (+ ?progr ?prognr))
    
    (bind ?fz-prognr (cost-fv ?prognr 30))
    (bind ?fz-progr (cost-fv ?progr 30))
    (bind ?fz-prog (fuzzysum ?fz-progr ?fz-prognr))
    
     (modify ?miss (program-non-recurring-cost# ?prognr) (program-non-recurring-cost ?fz-prognr)
         (program-recurring-cost# ?progr) (program-cost# ?prog) (program-recurring-cost ?fz-progr) (program-cost ?fz-prog) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-program-overhead-cost) " " ?fh "}")))
    )


; ********************
; Operations cost (salience -5)
; ********************

(defrule FUZZY-COST-ESTIMATION::estimate-operations-cost-std
    "This rule estimates operations cost using NASAs MOCM"
    (declare (salience -5))
    ?miss <- (MANIFEST::Mission (satellite-cost# ?sat&~nil) (operations-cost# nil) 
        (lifetime ?life &~nil) (program-cost# ?prog&~nil) (IAT-cost# ?iat&~nil)
        (sat-data-rate-per-orbit# ?rbo&nil) (factHistory ?fh))
    =>
    (bind ?total-cost (+ ?sat ?prog ?iat))
    (bind ?total-cost (* ?total-cost 0.001097)); correct for inflation and transform to $M
    (bind ?ops-cost (* (* 0.035308 (** ?total-cost 0.928)) ?life)); NASA MOCM in FY04$M
    (bind ?ops-cost (/ ?ops-cost 0.001097)); back to FY00$k
    (modify ?miss (operations-cost# ?ops-cost) (operations-cost (cost-fv ?ops-cost 30)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-operations-cost-std) " " ?fh "}")))
    )


(defrule FUZZY-COST-ESTIMATION::estimate-operations-cost-with-ground-station-penalty
    "This rule estimates operations cost using NASAs MOCM"
    (declare (salience -5))
    ?miss <- (MANIFEST::Mission (satellite-cost# ?sat&~nil) (operations-cost# nil) 
        (lifetime ?life &~nil) (program-cost# ?prog&~nil) (IAT-cost# ?iat&~nil)
        (sat-data-rate-per-orbit# ?rbo&~nil) (factHistory ?fh))
    =>
    (bind ?total-cost (+ ?sat ?prog ?iat))
    (bind ?total-cost (* ?total-cost 0.001097)); correct for inflation and transform to $M
    (bind ?ops-cost (* (* 0.035308 (** ?total-cost 0.928)) ?life)); NASA MOCM in FY04$M
    (bind ?ops-cost (/ ?ops-cost 0.001097)); back to FY00$k
    (if (> ?rbo (* 5 60 700 (/ 1 8192))) then (bind ?pen 10.0) else (bind ?pen 1.0))
    ;(printout t "penalty =" ?pen crlf)
    (modify ?miss (operations-cost# (* ?ops-cost ?pen)) (operations-cost (cost-fv (* ?ops-cost ?pen) 30)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-operations-cost-with-ground-station-penalty) " " ?fh "}")))
    )

; ********************
; Total cost (salience -10)
; ********************
(defquery COST-ESTIMATION::search-instrument-TRL
    (declare (variables ?ins))
    (DATABASE::Instrument (Name ?ins) (Technology-Readiness-Level ?trl))
    )


(deffunction get-instrument-trl (?ins)
    (bind ?result (run-query* COST-ESTIMATION::search-instrument-TRL ?ins))
    (?result next)
    (bind ?trl (?result getDouble trl))
    (return ?trl)
    )

(deffunction get-instrument-list-trls (?list)
    (bind ?trls (new java.util.ArrayList))
    (foreach ?ins ?list
        (bind ?trl (get-instrument-trl ?ins))
        (?trls add ?trl)
        )
    (return ?trls)
    )

(deffunction p*$ (?x ?y) 
    (printout t " p*$ " ?x ?y crlf) 
    (if (not (listp ?x)) then (return (* ?x ?y))) 
    (bind ?z (create$ )) 
    (for (bind ?i 1) (<= ?i (length$ ?x)) (++ ?i)
    (printout t ?i crlf) (bind ?z (insert$ ?z ?i (* (eval (nth$ ?i ?x)) (eval (nth$ ?i ?y))))))
      
    (return ?z))

(defrule FUZZY-COST-ESTIMATION::estimate-total-mission-cost-with-overruns
    "This rule estimates total mission cost adding an overrun which is proportional to 
    the expected schedule slippage, which in turn is a function of the TRL of the less 
    mature instrument in the payload"
    
    (declare (salience -10))
    ?miss <- (MANIFEST::Mission (satellite-cost# ?sat&~nil) (operations-cost# ?ops&~nil) 
        (launch-cost# ?launch&~nil) (program-cost# ?prog&~nil) (IAT-cost# ?iat&~nil)
        (mission-cost# nil) (instruments $?ins) (partnership-type $?prt&:(eq (length$ ?prt) 0)) (factHistory ?fh)
        )
    =>
    ;(printout t $?ins crlf)
    (bind ?mission-cost (+ ?sat ?prog ?iat ?ops (* 1000 ?launch)))
    (bind ?mission-cost (/ ?mission-cost 1000)); to $M
    (bind ?over (compute-cost-overrun (get-instrument-list-trls ?ins)))
    (modify ?miss (mission-cost# (* ?mission-cost (+ 1 ?over))) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-total-mission-cost-with-overruns) " " ?fh "}")))
    )



(defrule FUZZY-COST-ESTIMATION::estimate-total-mission-cost-with-overruns-when-partnership
    "This rule estimates total mission cost adding an overrun which is proportional to 
    the expected schedule slippage, which in turn is a function of the TRL of the less 
    mature instrument in the payload. Partnerships with internationals are taken into 
    account"
    
    (declare (salience -10))
    ?miss <- (MANIFEST::Mission (satellite-cost# ?sat&~nil) (operations-cost# ?ops&~nil) 
        (launch-cost# ?launch&~nil) (program-cost# ?prog&~nil) (IAT-cost# ?iat&~nil)
        (payload-cost# ?payl&~nil) (bus-cost# ?bus&~nil) 
        (mission-cost# nil) (instruments $?ins) (partnership-type $?prt&:(> (length$ ?prt) 0)) (factHistory ?fh)
        )
    =>
    ;(printout t $?ins crlf)
    ;(bind ?costs (create$ ?sat ?prog ?iat ?ops (* 1000 ?launch)))
    (bind ?costs (create$ ?payl ?bus (* 1000 ?launch) ?prog ?iat ?ops))
    
    (bind ?mission-cost (dot-product$ ?costs ?prt))
    ;(bind ?mission-cost (+ ?sat ?prog ?iat ?ops (* 1000 ?launch)))
    (bind ?mission-cost (/ ?mission-cost 1000)); to $M
    
    (bind ?over (compute-cost-overrun (get-instrument-list-trls ?ins)))
    ;(printout t ?mission-cost " " ?over " " (* ?mission-cost (+ 1 ?over)) crlf)
    (modify ?miss (mission-cost# (* ?mission-cost (+ 1 ?over))) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-total-mission-cost-with-overruns-when-partnership) " " ?fh "}")))
    
    )


(defrule FUZZY-COST-ESTIMATION::estimate-total-mission-cost-non-recurring
    "Non recurring cost"
    
    (declare (salience -10))
    ?miss <- (MANIFEST::Mission (bus-non-recurring-cost# ?bus&~nil) (payload-non-recurring-cost# ?payl&~nil) 
        (program-non-recurring-cost# ?prog&~nil) (IAT-non-recurring-cost# ?iat&~nil)
        (bus-non-recurring-cost ?fz-bus) (payload-non-recurring-cost ?fz-payl) 
        (program-non-recurring-cost ?fz-prog) (IAT-non-recurring-cost ?fz-iat)
        (mission-non-recurring-cost# nil) (factHistory ?fh))
        
    =>
    (bind ?mission-cost (/ (+ ?bus ?payl ?prog ?iat) 1000)); to $M
    (bind ?fz-mission-cost (fuzzyscprod (fuzzysum$ 
                (create$ ?fz-bus ?fz-payl ?fz-prog ?fz-iat)) 0.001)); to $M
    (modify ?miss (mission-non-recurring-cost ?fz-mission-cost) (mission-non-recurring-cost# ?mission-cost) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-total-mission-cost-non-recurring) " " ?fh "}")))
    )

(defrule FUZZY-COST-ESTIMATION::estimate-total-mission-cost-recurring
    "Non recurring cost"
    
    (declare (salience -10))
    ?miss <- (MANIFEST::Mission (bus-recurring-cost# ?bus&~nil) (payload-recurring-cost# ?payl&~nil) 
        (program-recurring-cost# ?prog&~nil) (IAT-recurring-cost# ?iat&~nil) (operations-cost# ?ops&~nil)
        (launch-cost# ?launch&~nil)
        (bus-recurring-cost ?fz-bus) (payload-recurring-cost ?fz-payl) 
        (program-recurring-cost ?fz-prog) (IAT-recurring-cost ?fz-iat) (operations-cost ?fz-ops)
        (launch-cost ?fz-launch&~nil) 
         (num-of-planes# ?np&~nil) (num-of-sats-per-plane# ?ns&~nil) 
        (mission-recurring-cost# nil) (factHistory ?fh))
        
    =>
    (bind ?mission-cost (/ (+ ?bus ?payl ?prog ?iat ?ops) 1000)); to $M
	(bind ?fz-mission-cost (fuzzyscprod (fuzzysum$ 
                (create$ ?fz-bus ?fz-payl ?fz-prog ?fz-iat ?fz-ops)) 0.001)); to $M
	
    (bind ?S 0.95); 95% learning curve, means doubling N reduces average cost by 5% (See  SMAD p 809)
    (bind ?N (* ?np ?ns)) 
    (bind ?B (- 1 (/ (log (/ 1 ?S)) (log 2))))
    (bind ?L (** ?N ?B))
    (bind ?total-cost (* ?L ?mission-cost))  
    (bind ?fz-total-cost (fuzzyscprod ?fz-mission-cost ?L))
    (modify ?miss (mission-recurring-cost# (+ ?total-cost ?launch))
        (mission-recurring-cost (fuzzysum ?fz-total-cost ?fz-launch)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-total-mission-cost-recurring) " " ?fh "}")))
    )

(defrule FUZZY-COST-ESTIMATION::estimate-lifecycle-mission-cost
    ?miss <- (MANIFEST::Mission (mission-recurring-cost# ?rec&~nil) (mission-recurring-cost ?fz-rec)
         (mission-non-recurring-cost ?fz-nr) (mission-non-recurring-cost# ?nr&~nil) (lifecycle-cost# nil) (factHistory ?fh))
    => (modify ?miss (lifecycle-cost# (+ ?rec ?nr)) (lifecycle-cost (fuzzysum ?fz-rec ?fz-nr)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-COST-ESTIMATION::estimate-lifecycle-mission-cost) " " ?fh "}")))
    )



(defquery COST-ESTIMATION::search-cost-breakdown
    (declare (variables ?name))
    (MANIFEST::Mission (Name ?name) (mission-cost# ?total) (payload-cost# ?payl) 
        (bus-cost# ?bus)  (launch-cost# ?launch)  (program-cost# ?prog) (IAT-cost# ?iat) (operations-cost# ?ops))
    )

(deffunction get-cost-breakdown (?miss)
    (bind ?results (run-query* COST-ESTIMATION::search-cost-breakdown ?miss))
    (while (?results next)
        (bind ?list (create$ (?results getDouble payl) (?results getDouble bus) 
                (* 1000 (?results getDouble launch)) (?results getDouble prog)
                 (?results getDouble iat) (?results getDouble ops) 
                (* 1000 (?results getDouble total))))
        )
    (return (map (lambda (?x) (return (/ ?x 1000))) ?list))
    )
;(defrule FUZZY-COST-ESTIMATION::estimate-programmatic-risk
;    "This rule assesses programmatic risk from initial TRL of the instruments"
;    )
    
 