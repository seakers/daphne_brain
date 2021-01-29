;; *********************************
;; Mission - mission inheritance
;; *********************************

(batch (str-cat ?*app_path* "/clp/orbit_rules.clp"))

(defquery MANIFEST::search-instrument-by-name   (declare (variables ?name))
    (DATABASE::Instrument (Name ?name) (mass# ?m) (average-power# ?p) (peak-power# ?pp) 
        (average-data-rate# ?rb) (dimension-x# ?dx) (dimension-y# ?dy) (characteristic-power# ?ppp)  
        (dimension-z# ?dz) (cost# ?c) (cost ?fz-c))
    )
(defquery MANIFEST::search-instrument-by-name-manifest   (declare (variables ?name))
    (CAPABILITIES::Manifested-instrument (Name ?name) (mass# ?m) (average-power# ?p) (peak-power# ?pp) 
        (average-data-rate# ?rb) (dimension-x# ?dx) (dimension-y# ?dy) (characteristic-power# ?ppp)  
        (dimension-z# ?dz) (cost# ?c) (cost ?fz-c))
    )
(deffunction get-instrument-cost (?instr)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result getDouble c))
    )
(deffunction get-instrument-cost-manifest (?instr)
    (bind ?result (run-query* MANIFEST::search-instrument-by-name-manifest ?instr))
    (?result next)
    (return (?result getDouble c))
    )
(deffunction get-instrument-fuzzy-cost (?instr)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result get fz-c))
    )
(deffunction get-instrument-fuzzy-cost-manifest (?instr)
    (bind ?result (run-query* MANIFEST::search-instrument-by-name-manifest ?instr))
    (?result next)
    (return (?result get fz-c))
    )

(deffunction get-instrument-mass (?instr)
    ;(printout t "get-instrument-mass " ?instr (str-length ?instr) crlf)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result getDouble m))
    )


(deffunction get-instrument-peak-power (?instr)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result getDouble ppp))
    )


(deffunction get-instrument-power (?instr)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result getDouble ppp))
    )

(deffunction get-instrument-datarate (?instr)
    (bind ?result (run-query* search-instrument-by-name ?instr))
    (?result next)
    (return (?result getDouble rb))
    )

(deffunction compute-payload-mass($?payload)(bind ?mass 0)(foreach ?instr $?payload (bind ?mass (+ ?mass (get-instrument-mass ?instr)))
        )
    (return ?mass)
    )

(deffunction compute-payload-power ($?payload)
    (bind ?power 0)
    (foreach ?instr $?payload (bind ?power (+ ?power (get-instrument-power ?instr)))
        )
    (return ?power)
    )

(deffunction compute-payload-peak-power ($?payload)
    (bind ?power 0)
    (foreach ?instr $?payload
        (bind ?power (+ ?power (get-instrument-peak-power ?instr)))
        )
    (return ?power)
    )

(deffunction compute-payload-data-rate ($?payload)
    (bind ?rb 0)
    (foreach ?instr $?payload
        (bind ?rb (+ ?rb (get-instrument-datarate ?instr)))
        )
    (return ?rb)
    )

(deffunction compute-payload-dimensions (?payload)
    ;;(printout t "compute-payload-dimensions" ?payload crlf)
    (bind ?X 0) (bind ?Y 0) (bind ?Z 0) (bind ?nadir-area 0)
    (foreach ?instr ?payload
        (bind ?result (run-query* search-instrument-by-name ?instr))
        (?result next)
        (bind ?dx (?result getDouble dx))
        (bind ?dy (?result getDouble dy))
        (bind ?dz (?result getDouble dz))
        (bind ?X (max ?X ?dx))
        (bind ?Y (max ?Y ?dy))
        (bind ?nadir-area  (+ ?nadir-area  (* ?dx ?dy)))
        (bind ?Z (max ?Z ?dz))
        )
    (bind ?max-dim (max ?X ?Y ?Z))
    (return (create$ ?max-dim ?nadir-area ?Z))
    )

; populate payload mass
(defrule MANIFEST::populate-payload-mass
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (instruments $?payload) (payload-mass# nil) (factHistory ?fh))
    =>
    (bind ?m (compute-payload-mass $?payload))
    (modify ?miss (payload-mass# ?m) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::populate-payload-mass) " " ?fh "}")))
    )
 


; populate payload power
(defrule MANIFEST::populate-payload-power
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (instruments $?payload) (payload-power# nil) (factHistory ?fh))
    =>
    (bind ?p (compute-payload-power $?payload))
    (modify ?miss (payload-power# ?p) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::populate-payload-power) " " ?fh "}")))
    )

(defrule MANIFEST::populate-payload-peak-power
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (instruments $?payload) (payload-peak-power# nil) (factHistory ?fh))
    =>
    (bind ?peak (compute-payload-peak-power $?payload))
    (modify ?miss (payload-peak-power# ?peak)(factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::populate-payload-peak-power) " " ?fh "}"))))
    
; populate payload data rate
(defrule MANIFEST::populate-payload-data-rate
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (instruments $?payload) (orbit-period# ?P&~nil) (payload-data-rate# nil) (factHistory ?fh))
    =>
    (bind ?rb (compute-payload-data-rate $?payload))
    (bind ?rbo (/ (* ?rb 1.2 ?P) (* 1024 8))); (GByte/orbit) 20% overhead
    (modify ?miss (payload-data-rate# ?rb) (sat-data-rate-per-orbit# ?rbo) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::populate-payload-data-rate) " " ?fh "}")))
    )

; populate payload dimensions
(defrule MANIFEST::populate-payload-dimensions
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (instruments $?payload) (payload-dimensions# $?pd) (factHistory ?fh))
    (test (eq (length$ ?pd) 0))
    =>
    (bind ?dim (compute-payload-dimensions ?payload))
    (modify ?miss (payload-dimensions# ?dim) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::populate-payload-dimensions) " " ?fh "}")))
    )

;; **********************************
;; Mission ==> Instrument inheritance (control)
;; **********************************

(defrule MANIFEST0::assert-manifested-instruments
    (declare (salience 20))

    ?miss <- (MANIFEST::Mission (Name ?name) (mission-architecture ?arch) (num-of-planes# ?nplanes) (num-of-sats-per-plane# ?nsats) (orbit-altitude# ?h) (orbit-inclination ?inc) (instruments $?list-of-instruments))
    
       =>
    (foreach ?x $?list-of-instruments (assert (CAPABILITIES::Manifested-instrument (Name ?x) (flies-in ?name)  (mission-architecture ?arch) (num-of-planes# ?nplanes) (num-of-sats-per-plane# ?nsats) (num-of-planes# ?nplanes) (orbit-altitude# ?h) (orbit-inclination ?inc) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST2::assert-manifested-instruments) " A" (call ?miss getFactId) "}")))))
    ;(assert (SYNERGIES::cross-registered-instruments (instruments ?list-of-instruments) (degree-of-cross-registration spacecraft)))
    )         


;; **********************************
;; Mission ==> Instrument inheritance (calculated attributes)
;; **********************************

(defrule MANIFEST::get-instrument-spectral-bands-from-database
    ?instr <- (CAPABILITIES::Manifested-instrument (Name ?name) (spectral-bands $?sb&:(< (length$ $?sb) 1)) (factHistory ?fh1))
    ?sub <- (DATABASE::Instrument (Name ?name) (spectral-bands $?sb2&:(>= (length$ $?sb2) 1)))
    =>
    (modify ?instr (spectral-bands $?sb2) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::get-instrument-spectral-bands-from-database) " " ?fh1 " S" (call ?sub getFactId) "}")))
    )

;(defquery DATABASE::get-revisit-times
;    (declare (variables ?))
;    (DATABASE::Revisit-time-of (mission-architecture ?arch) 
;        (num-of-sats-per-plane# ?nsats) (num-of-planes# ?nplanes) (orbit-altitude# ?h) 
;        (orbit-inclination ?inc) (instrument-field-of-view# ?fov) 
;        (avg-revisit-time-global# ?revtime-global)
;         (avg-revisit-time-tropics# ?revtime-tropics)
;         (avg-revisit-time-northern-hemisphere# ?revtime-NH)
;         (avg-revisit-time-southern-hemisphere# ?revtime-SH)
;         (avg-revisit-time-cold-regions# ?revtime-cold) 
;        (avg-revisit-time-US# ?revtime-US))
;    )

(deffunction round-to-5deg (?fov)
    (return (* 5 (round (/ ?fov 5))))
    )

(defrule MANIFEST::get-instrument-revisit-times-from-database
    (declare (salience 5))
    ?instr <- (CAPABILITIES::Manifested-instrument (Name ?name) (Field-of-view# ?fov&~nil)
         (mission-architecture ?arch) (num-of-planes# ?nplanes&~nil)
         (num-of-sats-per-plane# ?nsats&~nil) 
        (orbit-altitude# ?h&~nil) (orbit-RAAN ?raan&~nil) (orbit-inclination ?inc&~nil)
        (avg-revisit-time-global# nil) (avg-revisit-time-tropics# nil)
         (avg-revisit-time-northern-hemisphere# nil) 
        (avg-revisit-time-southern-hemisphere# nil) 
        (avg-revisit-time-cold-regions# nil) (avg-revisit-time-US# nil) (factHistory ?fh1))
    ?sub <- (DATABASE::Revisit-time-of (mission-architecture ?arch) (num-of-sats-per-plane# ?nsats) 
        (num-of-planes# ?nplanes) (orbit-altitude# ?h) (orbit-inclination ?inc) 
        (instrument-field-of-view# ?fov2&:(eq ?fov2 (round-to-5deg ?fov))) (orbit-raan ?raan2)  (avg-revisit-time-global# ?revtime-global) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH) (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US) )
     (test (or (eq ?raan ?raan2) (eq ?raan NA)))
    =>
    (modify ?instr (avg-revisit-time-global# ?revtime-global) (avg-revisit-time-tropics# ?revtime-tropics) (avg-revisit-time-northern-hemisphere# ?revtime-NH) (avg-revisit-time-southern-hemisphere# ?revtime-SH) (avg-revisit-time-cold-regions# ?revtime-cold) (avg-revisit-time-US# ?revtime-US) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::get-instrument-revisit-times-from-database) " " ?fh1 " S" (call ?sub getFactId) "}")))
    )

(defrule MANIFEST::compute-hsr-cross-track-from-instrument-and-orbit 
    "Compute horizontal spatial resolution from instrument angular resolution 
    and orbit altitude"
    ?instr <- (CAPABILITIES::Manifested-instrument (orbit-altitude# ?h&~nil) (Angular-resolution-azimuth# ?ara&~nil) 
        (Horizontal-Spatial-Resolution-Cross-track# nil) (factHistory ?fh))
    =>
    (modify ?instr (Horizontal-Spatial-Resolution-Cross-track# (* 1000 ?h (* ?ara (/ (pi) 180)) ))  (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-hsr-cross-track-from-instrument-and-orbit) " " ?fh "}")))
    )

(defrule MANIFEST::compute-hsr-along-track-from-instrument-and-orbit 
    "Compute horizontal spatial resolution from instrument angular resolution 
    and orbit altitude"
    ?instr <- (CAPABILITIES::Manifested-instrument (orbit-altitude# ?h&~nil) (Angular-resolution-elevation# ?are&:(neq ?are nil)) (Horizontal-Spatial-Resolution-Along-track# nil) (factHistory ?fh))
    =>
    (modify ?instr (Horizontal-Spatial-Resolution-Along-track# (* 1000 ?h (* ?are (/ (pi) 180)) )) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-hsr-along-track-from-instrument-and-orbit) " " ?fh "}")) )
    )

(defrule MANIFEST::compute-hsr-from-instrument-and-orbit 
    "Compute horizontal spatial resolution hsr and hsr2 from instrument angular resolution 
    and orbit altitude"
    ?instr <- (CAPABILITIES::Manifested-instrument (orbit-altitude# ?h&~nil) (Angular-resolution# ?are&:(neq ?are nil)) (Horizontal-Spatial-Resolution# nil) (factHistory ?fh))
    =>
    (modify ?instr (Horizontal-Spatial-Resolution# (* 1000 ?h (* ?are (/ (pi) 180)) )) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-hsr-from-instrument-and-orbit) " " ?fh "}")))
    )

(defrule MANIFEST::fill-in-hsr-from-directional-hsrs
    "If along-track and cross-track spatial resolutions are known and identical, then 
    horizontal spatial resolution is equal to them"
    (declare (salience -2))
    ?instr <- (CAPABILITIES::Manifested-instrument (Horizontal-Spatial-Resolution-Cross-track# ?cr&~nil)
        (Horizontal-Spatial-Resolution-Along-track# ?al&~nil&?cr) (Horizontal-Spatial-Resolution# nil) (factHistory ?fh))
    =>
    (modify ?instr (Horizontal-Spatial-Resolution# ?cr)(factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::fill-in-hsr-from-directional-hsrs) " " ?fh "}")))
    )


;(defrule MANIFEST::compute-swath-from-instrument-and-orbit 
;    "Compute swath from instrument field of regard 
;    and orbit altitude"
;    
;    ?instr <- (CAPABILITIES::Manifested-instrument (orbit-altitude# ?h&~nil) 
;        (Field-of-regard# ?for&~nil) (Swath# nil))
;    =>
;    (bind ?sw (* 2 ?h (matlabf tan (* ?for (/ (pi) 360) )))) 
;    (modify ?instr (Swath# ?sw) ) 
;    )

(defrule MANIFEST::compute-fov-from-angular-res-and-npixels-square 
    "Compute field of view in degrees from angular resolution (IFOV)
    and number of pixels for a square image"
    (declare (salience 4))
    ?instr <- (CAPABILITIES::Manifested-instrument  (Field-of-view# nil) 
        (Angular-resolution-azimuth# nil) (Angular-resolution-elevation# nil)
        (Angular-resolution# ?ifov&~nil) (num-pixels# ?npix&~nil) (factHistory ?fh) ) ; only square images
    =>
	(bind ?fov (* ?ifov ?npix)); 
    (modify ?instr (Field-of-view# ?fov) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-fov-from-angular-res-and-npixels-square) " " ?fh "}")))
    )

(defrule MANIFEST::compute-fov-from-angular-res-and-npixels-elevation 
    "Compute field of view in degrees from angular resolution (IFOV)
    and number of pixels for the elevation direction in a rectangular image"
    (declare (salience 4))
    ?instr <- (CAPABILITIES::Manifested-instrument  (Field-of-view-elevation# nil) 
       (Angular-resolution-elevation# ?ara&~nil) (num-pixels-along-track# ?npix&~nil) (factHistory ?fh) )
    =>
	(bind ?fov (* ?ara ?npix)); 
    (modify ?instr (Field-of-view-elevation# ?fov) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-fov-from-angular-res-and-npixels-elevation) " " ?fh "}")))
    )

(defrule MANIFEST::compute-fov-from-angular-res-and-npixels-azimuth 
    "Compute field of view in degrees from angular resolution (IFOV)
    and number of pixels for the azimuth direction in a rectangular image"
    (declare (salience 4))
    ?instr <- (CAPABILITIES::Manifested-instrument  (Field-of-view-azimuth# nil) 
       (Angular-resolution-azimuth# ?ara&~nil) (num-pixels-cross-track# ?npix&~nil) (factHistory ?fh))
    =>
	(bind ?fov (* ?ara ?npix)); 
    (modify ?instr (Field-of-view-azimuth# ?fov) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-fov-from-angular-res-and-npixels-azimuth) " " ?fh "}")))
    )

(defrule MANIFEST::compute-for-from-fov-square 
    "Compute field of regard in degrees from field of view
    and off-axis scanning capability"
    (declare (salience 2))
    ?instr <- (CAPABILITIES::Manifested-instrument  (Field-of-regard# nil) 
        (Field-of-view# ?fov&~nil) (off-axis-angle-plus-minus# ?off-axis) (factHistory ?fh)) ; only square images
    =>
    
    ; if no scanning capability then FOR = FOV, else take into account scanning
    (if (neq ?off-axis nil) then
        (bind ?for (+ ?fov (* 2 ?off-axis)))
        else
        (bind ?for  ?fov); 
        )
	
    (modify ?instr (Field-of-regard# ?for) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-for-from-fov-square) " " ?fh "}")))
    )

(defrule MANIFEST::compute-revisit-time
    
    ?m <- (REQUIREMENTS::Measurement (taken-by ?ins) (avg-revisit-time-global# nil)
         (avg-revisit-time-tropics# nil) (avg-revisit-time-northern-hemisphere# nil)
        (avg-revisit-time-southern-hemisphere# nil) (avg-revisit-time-cold-regions# nil) 
        (avg-revisit-time-US# nil) (factHistory ?fh1))
    
    ?sub1 <- (CAPABILITIES::Manifested-instrument (Name ?ins) (num-of-planes# ?np) (num-of-sats-per-plane# ?ns)
         (orbit-altitude# ?h) (orbit-inclination ?inc) (Field-of-view# ?fov) )
    
    ?sub2 <- (DATABASE::Revisit-time-of (num-of-planes# ?np) (num-of-sats-per-plane# ?ns) (orbit-altitude# ?h)
         (orbit-inclination ?inc) (instrument-field-of-view# ?fov) 
         (avg-revisit-time-global# ?glob) (avg-revisit-time-tropics# ?trop)
         (avg-revisit-time-northern-hemisphere# ?nh)(avg-revisit-time-southern-hemisphere# ?sh) 
        (avg-revisit-time-cold-regions# ?cold) (avg-revisit-time-US# ?us) ) 
    => 
    (modify ?m (avg-revisit-time-global# ?glob) (avg-revisit-time-tropics# ?trop) (avg-revisit-time-northern-hemisphere# ?nh)
        (avg-revisit-time-southern-hemisphere# ?sh) (avg-revisit-time-cold-regions# ?cold) (avg-revisit-time-US# ?us) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-revisit-time) " " ?fh1 " S" (call ?sub1 getFactId) " S" (call ?sub2 getFactId) "}")))
    )

(defrule MANIFEST::adjust-power-with-orbit
    "Adjust average and peak power from characteristic orbit an power based on square law"
	(declare (salience 15))
    ?instr <- (CAPABILITIES::Manifested-instrument (average-power# nil) (orbit-altitude# ?h&~nil) (characteristic-power# ?p&~nil) (characteristic-orbit ?href&~nil) (factHistory ?fh))
    =>
	(bind ?zep (* ?p (** (/ ?h ?href) 2)))
    (modify ?instr (average-power# ?zep) (peak-power# ?zep)(factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::adjust-power-with-orbit) " " ?fh "}")))
    )

;; ********************************** 
;; **********************************
;; Cloud radars (e.g. Cloudsat, EarthCARE, ACE_RAD, TRMM PR)
;; **********************************
;; **********************************

(defrule MANIFEST::compute-cloud-radar-properties-vertical-spatial-resolution
    ?instr <- (CAPABILITIES::Manifested-instrument (Intent "Cloud profile and rain radars") 
        (bandwidth# ?B&~nil) (off-axis-angle-plus-minus# ?theta&~nil) (Vertical-Spatial-Resolution# nil) (factHistory ?fh))
    =>
    (bind ?range-res (/ 3e8 (* 2 ?B (sin ?theta))))
    (modify ?instr (Vertical-Spatial-Resolution# ?range-res) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-cloud-radar-properties-vertical-spatial-resolution) " " ?fh "}")))
    )

(defrule MANIFEST::compute-cloud-radar-properties-horizontal-spatial-resolution
    ?instr <- (CAPABILITIES::Manifested-instrument  (Intent "Cloud profile and rain radars")
         (frequency# ?f&~nil) (Aperture# ?D) (orbit-altitude# ?h&~nil) (Horizontal-Spatial-Resolution# nil) (factHistory ?fh))
    =>
    (bind ?hsr (* 1000 (/ 3e8 (* ?D ?f)) ?h)); hsr = lambda/D*h, lambda=c/f
    (modify ?instr (Horizontal-Spatial-Resolution# ?hsr) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-cloud-radar-properties-horizontal-spatial-resolution) " " ?fh "}")))
    )

(defrule MANIFEST::compute-cloud-radar-properties-swath
    ?instr <- (CAPABILITIES::Manifested-instrument (Intent "Cloud profile and rain radars") 
        (off-axis-angle-plus-minus# ?theta&~nil) (scanning conical) (orbit-altitude# ?h&~nil) (Swath# nil) (factHistory ?fh))
    =>
    (bind ?sw (* 2 ?h (tan ?theta ))); hsr = lambda/D*h, lambda=c/f
    (modify ?instr (Swath# ?sw) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-cloud-radar-properties-swath) " " ?fh "}")))
    )
;; ********************************** 
;; **********************************
;; Radar altimeters (e.g. Jason, SWOT)
;; **********************************
;; **********************************

(defrule MANIFEST::compute-altimeter-horizontal-spatial-resolution
    ?instr <- (CAPABILITIES::Manifested-instrument  (Intent "Radar altimeter")
         (frequency# ?f&~nil) (Aperture# ?D) (orbit-altitude# ?h&~nil) (Horizontal-Spatial-Resolution# nil) (factHistory ?fh))
    =>
    (bind ?hsr (* 1000 (/ 3e8 (* ?D ?f)) ?h)); hsr = lambda/D*h, lambda=c/f
    (modify ?instr (Horizontal-Spatial-Resolution# ?hsr) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::compute-altimeter-horizontal-spatial-resolution) " " ?fh "}")))
    )

;; ********************************** 
;; **********************************
;; Passive microwave imaging radiometers (e.g. SMAP)
;; **********************************
;; **********************************


; *** LIDARS



;; probert-jones equation pr = pt*g^2*theta^2*pulse width*pi^3*k^2*L*Z/1024ln(2)/lambda^2/R^2


;; SYNERGIES:: dual frequency ==> Ka improves sensitiviyty in rain

;; SYNERGIES:: dual polarization allows particle shape and phase transition

;; SYNERGIES:: Doppler capability allows better accuracy cloud type, air motion, particle size

;; **********************************
;; Instrument ==> Instrument (calculated attributes) (Angular-resolution-azimuth# nil) (Angular-resolution-elevation# nil)
;; **********************************

;; for a sounder, vertical resolution is related to number of channels (although resolution can be traded for accuracy)



;; **********************************
;; Instrument ==> Measurement inheritance
;; **********************************
;; See excel, plus:



;; ****************
;; Rules for synthesis of alternative mission architectures trading accuracy for spatial resolution,
;; temporal resolution, or vertical spatial resolution. All these missions will be declared, and
;; rules can be added so that only one of each can be selected
(defrule CAPABILITIES-UPDATE::basic-diurnal-cycle
?meas<- (REQUIREMENTS::Measurement (diurnal-cycle nil) (orbit-inclination ?inc&~nil) (orbit-RAAN ?raan&~nil) (factHistory ?fh))
=>
(if (eq ?inc polar) then (bind ?dc variable) else (bind ?dc (eval (str-cat ?raan "-only"))))
 (modify ?meas (diurnal-cycle ?dc)(factHistory (str-cat "{R" (?*rulesMap* get CAPABILITIES-UPDATE::basic-diurnal-cycle) " " ?fh "}")) ) )
 
 
 
 
 