;(batch templates.clp)   
;(batch functions.clp)

;; ***************************
;; CAPABILITY RULES
;; ***************************


(defrule CAPABILITIES::passive-optical-instruments-cannot-measure-in-dark
    "Passive optical instruments cannot take their measurements in DD RAANs"
    (declare (salience 10))
    ?c <- (CAPABILITIES::can-measure (instrument ?ins) (orbit-RAAN DD) (can-take-measurements yes) (factHistory ?fh1))
    ?sub <- (DATABASE::Instrument (Name ?ins) (Illumination Passive) (Spectral-region ?sr) )
    (test (eq (sub-string 1 (min (str-length ?sr) 3) ?sr) "opt"))
    =>
    ;(printout t cannot-measure-in-dark " " ?ins " " ?sr crlf)
    (modify ?c (can-take-measurements no) (reason "Passive optical instruments cannot take their measurements in DD RAANs") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::passive-optical-instruments-cannot-measure-in-dark) " " ?fh1 " S" (call ?sub getFactId) "}")))
    )

(defrule CAPABILITIES::chemistry-instruments-prefer-PM-orbits-effect-on-science-tropo
    "Decrease sensitivity of chemistry instruments flying in AM orbits"
    (declare (salience 10))
    ?i <- (CAPABILITIES::Manifested-instrument (Name ?ins) (Concept ?c) (orbit-RAAN AM) (sensitivity-in-low-troposphere-PBL High) (factHistory ?fh))
    (or 
        (test (neq (str-index "chemistry" ?c) FALSE))
        (test (neq (str-index "pollut" ?c) FALSE))
        )
    =>
    ;(printout t "Decrease sensitivity of chemistry instruments flying in AM orbits " ?ins " " crlf)
    (modify ?i (sensitivity-in-low-troposphere-PBL Low) (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::chemistry-instruments-prefer-PM-orbits-effect-on-science-tropo) " " ?fh "}"))) 
    )

(defrule CAPABILITIES::chemistry-instruments-prefer-PM-orbits-effect-on-science-strato
    "Decrease sensitivity of chemistry instruments flying in AM orbits"
    (declare (salience 10))
    ?i <- (CAPABILITIES::Manifested-instrument (Name ?ins) (Concept ?c) (orbit-RAAN AM) (sensitivity-in-upper-troposphere-and-stratosphere High) (factHistory ?fh))
    (or 
        (test (neq (str-index "chemistry" ?c) FALSE))
        (test (neq (str-index "pollut" ?c) FALSE))
        )
    =>
    ;(printout t "Decrease sensitivity of chemistry instruments flying in AM orbits " ?ins " " crlf)
    (modify ?i (sensitivity-in-upper-troposphere-and-stratosphere Low) (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::chemistry-instruments-prefer-PM-orbits-effect-on-science-strato) " " ?fh "}"))) 
    )

(defrule CAPABILITIES::hires-passive-optical-imagers-prefer-AM-orbits-effect-on-science
    "Passive optical all purpose hi res imagers such as Landsat or ASTER must fly in AM orbits to decrease cloudiness"
    (declare (salience 10))
    ?c <- (CAPABILITIES::can-measure (instrument ?ins) (orbit-RAAN PM) (can-take-measurements yes) (factHistory ?fh1))
    ?sub <- (DATABASE::Instrument (Name ?ins) (Illumination Passive) (Spectral-region ?sr) (Intent "High resolution optical imagers") )
    (test (eq (sub-string 1 (min (str-length ?sr) 3) ?sr) "opt"))
    =>
    ;(printout t cannot-measure-in-dark " " ?ins " " ?sr crlf)
    (modify ?c (can-take-measurements no) (reason "Passive optical all purpose hi res imagers such as Landsat or ASTER must fly in AM orbits to decrease cloudiness")(factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::hires-passive-optical-imagers-prefer-AM-orbits-effect-on-science) " " ?fh1 " S" (call ?sub getFactId) "}")))
    )

(defrule CAPABILITIES::image-distortion-at-low-altitudes-in-side-looking-instruments
    "Passive optical instruments cannot take their measurements in DD RAANs"
    (declare (salience 10))
    ?c <- (CAPABILITIES::can-measure (instrument ?ins) (orbit-altitude# ?h&~nil&:(<= ?h 400)) (can-take-measurements yes) (factHistory ?fh1))
    ?sub <- (DATABASE::Instrument (Name ?ins) (Geometry slant) (Spectral-region ?sr))
    =>
    ;(printout t image-distortion " " ?ins crlf)
    (modify ?c (can-take-measurements no) (reason "Side-looking instruments suffer from image distortion at low altitudes") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::image-distortion-at-low-altitudes-in-side-looking-instruments) " " ?fh1 " ?S" (call ?sub getFactId) "}")))
    )

(defrule CAPABILITIES::two-lidars-at-same-frequency-cannot-work
    "Two lidars at same frequency can interfere with each other"
    (declare (salience 10))
    ?l1 <- (CAPABILITIES::can-measure (instrument ?ins1) (can-take-measurements yes) (factHistory ?fh1))
    ?l2 <- (CAPABILITIES::can-measure (instrument ?ins2&~?ins1) (can-take-measurements yes) (factHistory ?fh2))
    ?sub1 <- (DATABASE::Instrument (Name ?ins1) (Intent "Laser altimeters") (spectral-bands $?sr))
    ?sub2 <- (DATABASE::Instrument (Name ?ins2) (Intent "Laser altimeters") (spectral-bands $?sr))
    
    =>
    ;(printout t two-lidars-same-freq " " ?ins1 " " ?ins2 " " $?sr crlf)
    (modify ?l1 (can-take-measurements no) (reason "Two lidars at same frequency can interfere with each other") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::two-lidars-at-same-frequency-cannot-work) " " ?fh1 " S" (call ?l2 getFactId) " S" (call ?sub1 getFactId) " S" (call ?sub2 getFactId) "}")))
    (modify ?l2 (can-take-measurements no) (reason "Two lidars at same frequency can interfere with each other") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::two-lidars-at-same-frequency-cannot-work) " " ?fh2 " S" (call ?l1 getFactId) " S" (call ?sub1 getFactId) " S" (call ?sub2 getFactId) "}")))
    )

(defrule CAPABILITIES::resource-limitations-datarate
    (declare (salience 10))
    ?l1 <- (CAPABILITIES::can-measure (instrument ?ins1) (in-orbit ?miss) (can-take-measurements yes) (data-rate-duty-cycle# nil) (factHistory ?fh1))
    ?i1 <- (CAPABILITIES::Manifested-instrument (Name ?ins1&~nil) (flies-in ?miss&~nil) (factHistory ?fh2))
    ?sub <- (MANIFEST::Mission  (Name ?miss) (sat-data-rate-per-orbit# ?rbo&~nil) (factHistory ?fh3))
    =>
    (bind ?dc (min 1.0 (/ (* 1 7 60 500 (/ 1 8192)) ?rbo))); you get 1 7' pass at 500Mbps max
    (modify ?l1 (data-rate-duty-cycle# ?dc) (reason "Cumulative spacecraft data rate cannot be downloaded to ground stations") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::resource-limitations-datarate) " " ?fh1 " S" (call ?i1 getFactId) " S" (call ?sub getFactId) "}")))
	(modify ?i1 (data-rate-duty-cycle# ?dc) (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::resource-limitations-datarate) " " ?fh2 " S" (call ?l1 getFactId) " S" (call ?sub getFactId) "}")))
    ;(if (< ?dc 1.0) then (printout t "resource-limitations-datarate " ?ins1 " dc = " ?dc crlf))
    )

(defrule CAPABILITIES::resource-limitations-power
    (declare (salience 10))
    ?l1 <- (CAPABILITIES::can-measure (instrument ?ins1) (in-orbit ?miss) (can-take-measurements yes) (power-duty-cycle# nil) (factHistory ?fh1))
	?i1 <- (CAPABILITIES::Manifested-instrument (Name ?ins1&~nil) (flies-in ?miss&~nil) (factHistory ?fh2))
    ?sub <- (MANIFEST::Mission  (satellite-BOL-power# ?pow&~nil) (factHistory ?fh3))
    =>
    (bind ?dc (min 1.0 (/ 10000 ?pow)))
    (modify ?l1 (power-duty-cycle# ?dc) (reason "Cumulative spacecraft power exceeds 10kW") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::resource-limitations-power) " " ?fh1 " S" (call ?i1 getFactId) " S" (call ?sub getFactId) "}")))
	(modify ?i1 (power-duty-cycle# ?dc) (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::resource-limitations-power) " " ?fh2 " S" (call ?l1 getFactId) " S" (call ?sub getFactId) "}")))
    ;(if (< ?dc 1.0) then (printout t "resource-limitations-power " ?ins1 " dc = " ?dc crlf))
    )
        
;(defrule CAPABILITIES::get-instrument-revisit-times-from-database
;    (declare (salience 5))
;    ?instr <- (CAPABILITIES::Manifested-instrument (Name ?name) (Field-of-view# ?fov&~nil)
;         (mission-architecture ?arch) (num-of-planes# ?nplanes&~nil)
;         (num-of-sats-per-plane# ?nsats&~nil) 
;        (orbit-altitude# ?h&~nil) (orbit-RAAN ?raan&~nil) (orbit-inclination ?inc&~nil)
;        (avg-revisit-time-global# nil) (avg-revisit-time-tropics# nil)
;         (avg-revisit-time-northern-hemisphere# nil) 
;        (avg-revisit-time-southern-hemisphere# nil) 
;        (avg-revisit-time-cold-regions# nil) (avg-revisit-time-US# nil))
;    (DATABASE::Revisit-time-of (mission-architecture ?arch) (num-of-sats-per-plane# ?nsats) (num-of-planes# ?nplanes) (orbit-altitude# ?h) (orbit-inclination ?inc) (instrument-field-of-view# ?fov) (orbit-raan ?raan)  (avg-revisit-time-global# ?revtime-global) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH) (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US))
;    =>
;    (modify ?instr (avg-revisit-time-global# ?revtime-global) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH) (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US))
;    )

(defrule CAPABILITIES::cryospheric-instruments-want-polar-orbits
    "If a cryospheric instrument is flown on a non polar orbit then 
    it loses coverage of the polar regions"
    
    (declare (salience 10))
    ?c <- (CAPABILITIES::can-measure (instrument ?ins) (orbit-inclination ?inc&~polar) (can-take-measurements yes) (factHistory ?fh1))
    ?sub <- (DATABASE::Instrument (Name ?ins) (Concept ?co) (factHistory ?fh2))
    (test (neq (str-index "Primary application: ice" ?co) FALSE))
    =>
    ;(printout t cryospheric-instruments-want-polar-orbits crlf)
    (modify ?c (can-take-measurements no) (reason "If a cryospheric instrument is flown on a non polar orbit then 
    it loses coverage of the polar regions") (factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES::cryospheric-instruments-want-polar-orbits) " " ?fh1 " S" (call ?sub getFactId) "}")))
    )


(defrule CAPABILITIES-REMOVE-OVERLAPS::cross-registered-remove-overlaps
    ?s1 <- (SYNERGIES::cross-registered (measurements $?m1) (factHistory ?f1))
    (SYNERGIES::cross-registered (measurements $?m1) (factHistory ?f2&~?f1))
    =>
    (retract ?s1)
)

