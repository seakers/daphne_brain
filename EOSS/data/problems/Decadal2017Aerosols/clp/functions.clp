;; NOT USED
;(batch ".\\clp\\jess_functions.clp")


(deffunction update-objective-variable (?obj ?new-value) 
    "Update the value of the global variable with the new value only if it is better"
     (bind ?obj (max ?obj ?new-value)))

(deffunction ContainsRegion (?observed-region ?desired-region) 
    "Returns true if the observed region i.e. 1st param contains the desired region 
    i.e. 2nd param" 
    (bind ?tmp1 (eq ?observed-region Global)) 
    (bind ?tmp2 (eq ?desired-region ?observed-region)) 
    (if (or ?tmp1 ?tmp2) then 
        (return TRUE) 
        else (return FALSE)))

(defquery REQUIREMENTS::get-measurement-param-fov-and-orbit
(declare (variables ?param))
(REQUIREMENTS::Measurement (Parameter ?param) (Field-of-view# ?fov) (orbit-string ?orb))
)

(deffunction update-fovs (?param ?orbit-list)
(bind ?results (run-query* REQUIREMENTS::get-measurement-param-fov-and-orbit ?param))
(bind ?n (length$ ?orbit-list))
(bind ?fovs (repeat$ -1 ?n))
(bind ?some FALSE)
(while (?results next)
	(bind ?some TRUE)
	(bind ?fov (?results get fov))
	(bind ?orb (?results get orb))
	(for (bind ?i 1) (<= ?i ?n) (++ ?i)
		(if (eq (nth$ ?i ?orbit-list) ?orb) then
			(bind ?fovs (replace$ ?fovs ?i ?i (max (nth$ ?i ?fovs) ?fov)))))
)
(if (eq ?some FALSE) then (return FALSE) else (return ?fovs))
)

(deffunction compute-cost-overrun (?trls)
	(bind ?min-trl 10)
	(for (bind ?i 0) (< ?i (call ?trls size)) (++ ?i)
		(bind ?trl (call ?trls get ?i))
		(if (< ?trl ?min-trl) then (bind ?min-trl ?trl)))
	(bind ?rss (* 8.29 (exp (* -0.56 ?min-trl))))	
	(return (+ 0.017 (* 0.24 ?rss)))
)
(deffunction design-EPS (?Pavg_payload ?Ppeak_payload ?frac_sunlight ?worst_sun_angle ?period ?lifetime ?dry_mass ?DOD)
	; params
	;(printout t design-EPS " " ?Pavg_payload " " ?Ppeak_payload " " ?frac_sunlight " " ?worst_sun_angle " " ?period " " ?lifetime " " ?dry_mass " " ?DOD crlf)
	(bind ?Xe 0.65); % efficiency from solar arrays to battery to equipment (SMAD page 415)
	(bind ?Xd  0.85); % efficiency from solar arrays to equipment (SMAD page 415)
	(bind ?P0 253);% in W/m2, corresponds to GaAs, see SMAD page 412,
	(bind ?Id 0.77); % See SMAD page 412
	(bind ?degradation 0.0275); % Degradation of solar arrays performance in % per year, corresponds to multi-junction
	(bind ?Spec_power_SA 25); % in W per kg see SMAD chapter 11
	(bind ?n 0.9); % Efficiency of battery to load (SMAD page 422).
	(bind ?Spec_energy_density_batt 40); % In Whr/kg see SMAD page 420, corresponds to Ni-H2
	
	; solar arrays
	
	(bind ?Pavg_payload (/ ?Pavg_payload 0.4)); % 0.3 SMAD page 340 to take into account bus power
	(bind ?Ppeak_payload (/ ?Ppeak_payload 0.4)) % 0.3 SMAD page 340 to take into account bus power
	(bind ?Pd (+ (* 0.8 ?Pavg_payload) (* 0.2 ?Ppeak_payload)));
	(bind ?Pe ?Pd);
	(bind ?Td (* ?period ?frac_sunlight))
	(bind ?Te (- ?period ?Td));

	; What we need in terms of power from the SA
	(bind ?Psa (/ (+ (* ?Pe (/ ?Te ?Xe)) (* ?Pd (/ ?Td ?Xd))) ?Td)) ;(Pe.*Te./Xe+Pd.*Td./Xd)./Td;

	; What the SA technology can give
	(bind ?theta (to-rad ?worst_sun_angle)); % Worst case Sun angle
	;(printout t ?P0 " " Id " " ?theta " " crlf)
	(bind ?P_density_BOL (abs (* ?P0 ?Id (cos ?theta))));
	(bind ?Ld  (** (- 1 ?degradation) ?lifetime));
	(bind ?P_density_EOL (* ?P_density_BOL ?Ld));

	; Surface required
	(bind ?Asa (/ ?Psa ?P_density_EOL));

	; Power at BOL
	(bind ?P_BOL  (* ?P_density_BOL ?Asa));

	; Mass of the SA
	(bind ?mass_SA (/ ?P_BOL ?Spec_power_SA));% 1kg per 25W at BOL (See SMAD chapter 10).
	
	;; Batteries
	(bind ?Cr (/ (* ?Pe ?Te) (* 3600 ?DOD ?n)));%because period is in seconds
	(bind ?mass_batt (/ ?Cr ?Spec_energy_density_batt));

	;; Others: regulators, converters, wiring
	(bind ?mass_others (+ (* (+ 0.02  0.0125) ?P_BOL) (* 0.02 ?dry_mass)));%SMAD page 334, assume all the power is regulated and half is converted.

	;; Total subsystem mass
	(bind ?mass_EPS (+ ?mass_SA ?mass_batt ?mass_others));

	(bind ?design_EPS (create$ ?mass_EPS ?P_BOL ?Asa ?mass_SA))
	(return ?design_EPS)
)
