;(require* modules "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\modules.clp")
;(require* templates "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\templates.clp")
;(require* more-templates "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\more_templates.clp")
;(require* functions "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\functions.clp")


; ******************************************
;      ELECTRICAL POWER SUBSYSTEM DESIGN
;                  (2 rules)
; ******************************************

(defrule MASS-BUDGET::estimate-depth-of-discharge
    ?sat <- (MANIFEST::Mission (orbit-type ?typ&~nil) (orbit-RAAN ?raan&~nil)
        (depth-of-discharge nil) (factHistory ?fh))
    =>
    (modify ?sat (depth-of-discharge (get-dod ?typ ?raan)) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::estimate-depth-of-discharge) " " ?fh "}")))
    )

(defrule MASS-BUDGET::design-EPS
    ?miss<- (MANIFEST::Mission (payload-power# ?p&~nil) (EPS-mass# nil) (depth-of-discharge ?dod&~nil) 
        (orbit-semimajor-axis ?a&~nil) (orbit-type ?typ&~nil) 
        (worst-sun-angle ?angle&~nil) (fraction-sunlight ?frac&~nil) 
              (satellite-dry-mass ?m&~nil) (satellite-BOL-power# nil) (lifetime ?life&~nil) (factHistory ?fh))
    =>
    (bind ?list (design-EPS ?p ?p ?frac ?angle (orbit-period ?a) ?life ?m ?dod)) 
    (bind ?epsm (nth$ 1 ?list)) (bind ?pow (nth$ 2 ?list)) (bind ?area (nth$ 3 ?list)) (bind ?samass (nth$ 4 ?list))
    (modify ?miss (EPS-mass# ?epsm) (satellite-BOL-power# ?pow) (solar-array-area ?area) (solar-array-mass ?samass) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-EPS) " " ?fh "}")))
    )


; ******************************************
; SUPPORTING QUERIES AND FUNCTIONS
; ******************************************

(deffunction get-dod (?type ?raan) ; see SMAD Page 422
"This function estimates the depth of discharge of an orbit"
    
    (if (eq ?type GEO) then (bind ?dod 0.8)
        elif (and (eq ?type SSO) (eq ?raan DD)) then (bind ?dod 0.6)
        else (bind ?dod 0.4)
        )
    (return ?dod)
    )

