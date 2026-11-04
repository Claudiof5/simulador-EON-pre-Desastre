# Sources cited in the article

Every reference in `overleaf/references.bib`, numbered as in the compiled PDF, with a link and the sentences of `overleaf/main.tex` that cite it ("next:" marks a following sentence of the same paragraph that also describes the source).

Bibliographic metadata was checked against Crossref and every claim against the source's abstract (RFC 8001 and Rak 2021 against their full text). All references are consistent with their sources.

## The 4 sources that needed a closer look (checked)

- [x] **[13] Rak et al. (2021)**: Checked against the full text (abstract, §1, §2.2): concurrent and geographically correlated failures, potential data loss in DCs and the three phases are supported. The two general sentences were reworded to match. https://doi.org/10.1016/j.osn.2021.100619
- [x] **[15] Sahoo et al. (2025)**: Checked against the abstract: it supports the provider-neutral exchange and the sharing of abstracted information. The competition and feedback details now cite only Sahoo 2022. https://doi.org/10.1364/JOCN.561579
- [x] **[16] Shen et al. (2016)**: Checked against the abstract: the survey covers spectrum sharing among backup lightpaths (shared protection) and survivability of EONs. https://doi.org/10.1007/s11107-015-0532-0
- [x] **[18] Tornatore et al. (2020)**: Checked against the abstract: alert-based preparation, data evacuation from datacenters and reconfiguration of virtual networks to migrate data and VMs. https://doi.org/10.1007/978-3-030-44685-7_14

---

## [1] Ayoub et al. (2021). Online Virtual Machine Evacuation for Disaster Resilience in Inter-Data Center Networks
*IEEE Transactions on Network and Service Management* · key `ayoub2021evacuation`  
**Link:** https://doi.org/10.1109/TNSM.2021.3056766

**Cited in the paper:**
- [ ] line 70 (Introduction): "When a disaster can be forecast, the warning window can instead be used to evacuate critical data before the failure."
  - next: "To our knowledge, neither line of work models several providers with separate views that compete for the same spectrum."
- [ ] line 125 (Background and related work > Data evacuation in the warning window): "The closest line of work uses the warning itself, for example rapid data evacuation in optical cloud networks, early-warning data backup between interconnected datacenters, alert-based network reconfiguration and online evacuation of virtual machines."
  - next: "These works optimize evacuation over one network, without the competing providers and information-only cooperation of our setting."

## [2] Bonani et al. (2018). Classes of Service Defined by Soft Trunk Reservation Technique in Elastic Optical Networks
*Proc. 20th International Conference on Transparent Optical Networks (ICTON)* · key `bonani2018soft`  
**Link:** https://doi.org/10.1109/ICTON.2018.8473828

**Cited in the paper:**
- [ ] line 113 (Background and related work > Elastic optical networks): "Keeping part of the capacity of a link away from one class of traffic is known as trunk reservation; in flexible-grid networks it has been used to balance blocking among connections of different sizes and to define classes of service."
  - next: "Our mechanism uses a reservation of this kind; its novelty lies in where the reservation is legitimate and in who enforces it."

## [3] Callegati et al. (2014). Trunk Reservation for Fair Utilization in Flexible Optical Networks
*IEEE Communications Letters* · key `callegati2014trunk`  
**Link:** https://doi.org/10.1109/LCOMM.2014.040214.140058

**Cited in the paper:**
- [ ] line 113 (Background and related work > Elastic optical networks): "Keeping part of the capacity of a link away from one class of traffic is known as trunk reservation; in flexible-grid networks it has been used to balance blocking among connections of different sizes and to define classes of service."
  - next: "Our mechanism uses a reservation of this kind; its novelty lies in where the reservation is legitimate and in who enforces it."

## [4] Ceccarelli and Lee (2018). Framework for Abstraction and Control of TE Networks (ACTN)
*IETF RFC 8453* · key `rfc8453`  
**Link:** https://doi.org/10.17487/RFC8453 (also https://www.rfc-editor.org/rfc/rfc8453)

**Cited in the paper:**
- [ ] line 148 (Background and related work > Information disclosed by infrastructure owners): "Frameworks for abstraction and control of multi-customer transport networks expose selected, abstracted information to each customer."

## [5] Dantas (2026). Simulador EON pre-desastre: Multi-Provider Elastic Optical Network Simulator for the Disaster Warning Window
*Software* · key `simulator`  
**Link:** https://github.com/Claudiof5/simulador-EON-pre-Desastre

**Cited in the paper:**
- [ ] line 443 (Simulation setup > Simulator): "We use a discrete-event simulator written in Python with SimPy and NetworkX; its source code is publicly available."
  - next: "Traffic is generated before the simulation and stored with the scenario, so every variant of an experiment processes exactly the same requests at the same times."
  - next: "Since all metrics refer to requests created before t_d, each run starts at the beginning of the traffic and ends at t_d; requests created afterwards cannot change the measured results."
- [ ] line 450 (Simulation setup > Network and scenarios): "The physical topology is the USNET backbone (Figure (ref)), with the link lengths of the topology file in the simulator repository; Table (ref) lists the simulation parameters."
  - next: "The modulation factor of a path follows the distance thresholds of Section (ref); with these link lengths, most paths use factor 1 or 2."
  - next: "Every provider precomputes the k shortest paths by length between each pair of nodes of its overlay: 3 for normal operation and 10 for the warning window."

## [6] Ferdousi et al. (2015). Rapid Data Evacuation for Large-Scale Disasters in Optical Cloud Networks [Invited]
*Journal of Optical Communications and Networking* · key `evacuation2015rapid`  
**Link:** https://doi.org/10.1364/JOCN.7.00B163

**Cited in the paper:**
- [ ] line 70 (Introduction): "When a disaster can be forecast, the warning window can instead be used to evacuate critical data before the failure."
  - next: "To our knowledge, neither line of work models several providers with separate views that compete for the same spectrum."
- [ ] line 125 (Background and related work > Data evacuation in the warning window): "The closest line of work uses the warning itself, for example rapid data evacuation in optical cloud networks, early-warning data backup between interconnected datacenters, alert-based network reconfiguration and online evacuation of virtual machines."
  - next: "These works optimize evacuation over one network, without the competing providers and information-only cooperation of our setting."

## [7] Hagberg et al. (2008). Exploring Network Structure, Dynamics, and Function using NetworkX
*Proc. 7th Python in Science Conference (SciPy 2008)* · key `networkx`  
**Link:** https://doi.org/10.25080/TCWV9851

**Cited in the paper:**
- [ ] line 443 (Simulation setup > Simulator): "We use a discrete-event simulator written in Python with SimPy and NetworkX; its source code is publicly available."
  - next: "Traffic is generated before the simulation and stored with the scenario, so every variant of an experiment processes exactly the same requests at the same times."
  - next: "Since all metrics refer to requests created before t_d, each run starts at the beginning of the traffic and ends at t_d; requests created afterwards cannot change the measured results."

## [8] Jinno et al. (2010). Distance-Adaptive Spectrum Resource Allocation in Spectrum-Sliced Elastic Optical Path Network
*IEEE Communications Magazine* · key `jinno2010distance`  
**Link:** https://doi.org/10.1109/MCOM.2010.5534599

**Cited in the paper:**
- [ ] line 109 (Background and related work > Elastic optical networks): "In an EON, the spectrum of each fiber is divided into narrow frequency slots, and a connection (lightpath) occupies a block of adjacent slots sized to its bit rate."
  - next: "Routing and spectrum assignment (RSA) must respect two constraints: contiguity (the slots of a connection are adjacent) and continuity (the same slots are used on every link of the path)."
- [ ] line 111 (Background and related work > Elastic optical networks): "The number of slots also depends on the modulation format, which is limited by the transmission reach: shorter paths can use more efficient formats and therefore fewer slots."
  - next: "First-Fit, which tries candidate paths in order and takes the lowest-indexed block of free slots that fits, is a common baseline because of its simplicity."
- [ ] line 181 (Problem formulation > Physical network and spectrum): "The factor m((p)) is the capacity of a slot on path p relative to the most robust format, and it decreases with the length of the path."
  - next: "Its four levels can be read as formats carrying one to four bits per symbol (for example, BPSK, QPSK, 8-QAM and 16-QAM); the distance thresholds are a simplified reach model adopted in this work."
  - next: "For the same bit rate, a path with factor m therefore needs about 1/m as many slots as a path long enough to require the most robust format."

## [9] Jinno et al. (2009). Spectrum-Efficient and Scalable Elastic Optical Path Network: Architecture, Benefits, and Enabling Technologies
*IEEE Communications Magazine* · key `jinno2009spectrum`  
**Link:** https://doi.org/10.1109/MCOM.2009.5307468

**Cited in the paper:**
- [ ] line 109 (Background and related work > Elastic optical networks): "In an EON, the spectrum of each fiber is divided into narrow frequency slots, and a connection (lightpath) occupies a block of adjacent slots sized to its bit rate."
  - next: "Routing and spectrum assignment (RSA) must respect two constraints: contiguity (the slots of a connection are adjacent) and continuity (the same slots are used on every link of the path)."

## [10] Kaeval et al. (2022). Characterization of the Optical Spectrum as a Service
*Journal of Optical Communications and Networking* · key `kaeval2022osaas`  
**Link:** https://doi.org/10.1364/JOCN.454158

**Cited in the paper:**
- [ ] line 149 (Background and related work > Information disclosed by infrastructure owners): "Operators also offer optical spectrum as a service on open line systems; such services usually give each tenant its own part of the spectrum, whereas our model assumes that the spectrum of a link is shared by all providers that use it."
  - next: "Neither form of the disclosure names tenants directly, but neither is anonymous: a group that contains all providers but one can deduce the overlay of the remaining provider from the counts."

## [11] Little (1961). A Proof for the Queuing Formula: L=lambda W
*Operations Research* · key `little1961`  
**Link:** https://doi.org/10.1287/opre.9.3.383

**Cited in the paper:**
- [ ] line 420 (Cooperative corridor protection > Demand-driven reservation): "If migration were accepted at exactly that throughput, its mean occupied bandwidth would equal that throughput by Little's law: each request occupies b_r for a mean time h and delivers b_r h. Dividing by the capacity of one slot, m_o C, converts this bandwidth into slots."
  - next: "The rule is a heuristic."
  - next: "Migration is offered at more than the needed throughput, so its actual occupancy differs; the window is short and the needed throughput changes over time; and contiguity and the rounding of n(r,p) are ignored."

## [12] Ma et al. (2017). ε-Time Early Warning Data Backup in Disaster-Aware Optical Inter-Connected Data Center Networks
*Journal of Optical Communications and Networking* · key `backup2017earlywarning`  
**Link:** https://doi.org/10.1364/JOCN.9.000536

**Cited in the paper:**
- [ ] line 70 (Introduction): "When a disaster can be forecast, the warning window can instead be used to evacuate critical data before the failure."
  - next: "To our knowledge, neither line of work models several providers with separate views that compete for the same spectrum."
- [ ] line 125 (Background and related work > Data evacuation in the warning window): "The closest line of work uses the warning itself, for example rapid data evacuation in optical cloud networks, early-warning data backup between interconnected datacenters, alert-based network reconfiguration and online evacuation of virtual machines."
  - next: "These works optimize evacuation over one network, without the competing providers and information-only cooperation of our setting."

## [13] Rak et al. (2021). Disaster Resilience of Optical Networks: State of the Art, Challenges, and Opportunities ✅
*Optical Switching and Networking* · key `rak2021disaster`  
**Link:** https://doi.org/10.1016/j.osn.2021.100619

> **Checked:** Checked against the full text (abstract, §1, §2.2): concurrent and geographically correlated failures, potential data loss in DCs and the three phases are supported. The two general sentences were reworded to match.

**Cited in the paper:**
- [ ] line 68 (Introduction): "Disasters such as earthquakes, floods, wildfires and large power outages damage communication infrastructure in geographically correlated ways: many nodes and links fail together, and the data held in datacenters at the affected sites may be lost."
- [ ] line 118 (Background and related work > Disasters and the phases of resilience): "Disasters differ from isolated failures because they cause concurrent failures of many geographically correlated network elements, so protection schemes designed for single failures, such as dedicated or shared backup path protection, may not suffice."
- [ ] line 120 (Background and related work > Disasters and the phases of resilience): "Rak et al. distinguish proactive methods applied before a disaster, preparedness methods for the short interval between an early alert and the moment the disaster hits, and reactive post-disaster recovery."
  - next: "This work belongs to preparedness."

## [14] Sahoo et al. (2022). Strategic Cooperation among Datacenter Providers and Optical-Network Carriers for Disaster Recovery
*Proc. IEEE Global Communications Conference (GLOBECOM)* · key `sahoo2022cooperation`  
**Link:** https://doi.org/10.1109/GLOBECOM48099.2022.10001409

**Cited in the paper:**
- [ ] line 69 (Introduction): "Much of the work on disaster resilience in optical networks addresses restoration after the failure."
- [ ] line 137 (Background and related work > Cooperation across administrative domains): "Sahoo et al. restore datacenter services after a disaster through a third-party mediator, the Provider Neutral Exchange, which balances resources among datacenter providers that compete for them."
  - next: "Carriers evaluate the providers' requests and return feedback without disclosing confidential information such as their topology, and the cooperation improves service restoration."

## [15] Sahoo et al. (2025). Post-Disaster Cloud-Service Restoration through Datacenter-Carrier Cooperation ✅
*Journal of Optical Communications and Networking* · key `sahoo2025postdisaster`  
**Link:** https://doi.org/10.1364/JOCN.561579

> **Checked:** Checked against the abstract: it supports the provider-neutral exchange and the sharing of abstracted information. The competition and feedback details now cite only Sahoo 2022.

**Cited in the paper:**
- [ ] line 139 (Background and related work > Cooperation across administrative domains): "A later version formulates this cooperation as an optimization problem in which the exchange shares only abstracted information."
  - next: "Our setting shares the idea that cooperation is limited in what it reveals, but differs in three ways: it takes place in the warning window, no entity decides or balances allocations, and each provider acts only by restricting its own traffic."

## [16] Shen et al. (2016). Survivable Elastic Optical Networks: Survey and Perspective (Invited) ✅
*Photonic Network Communications* · key `shen2016survivable`  
**Link:** https://doi.org/10.1007/s11107-015-0532-0

> **Checked:** Checked against the abstract: the survey covers spectrum sharing among backup lightpaths (shared protection) and survivability of EONs.

**Cited in the paper:**
- [ ] line 118 (Background and related work > Disasters and the phases of resilience): "Disasters differ from isolated failures because they cause concurrent failures of many geographically correlated network elements, so protection schemes designed for single failures, such as dedicated or shared backup path protection, may not suffice."

## [17] Team SimPy (2023). SimPy: Discrete Event Simulation for Python, version 4.1.1
*Software* · key `simpy`  
**Link:** https://gitlab.com/team-simpy/simpy

**Cited in the paper:**
- [ ] line 443 (Simulation setup > Simulator): "We use a discrete-event simulator written in Python with SimPy and NetworkX; its source code is publicly available."
  - next: "Traffic is generated before the simulation and stored with the scenario, so every variant of an experiment processes exactly the same requests at the same times."
  - next: "Since all metrics refer to requests created before t_d, each run starts at the beginning of the traffic and ends at t_d; requests created afterwards cannot change the measured results."

## [18] Tornatore et al. (2020). Alert-Based Network Reconfiguration and Data Evacuation ✅
*Guide to Disaster-Resilient Communication Networks* · key `alertbased2020evacuation`  
**Link:** https://doi.org/10.1007/978-3-030-44685-7_14

> **Checked:** Checked against the abstract: alert-based preparation, data evacuation from datacenters and reconfiguration of virtual networks to migrate data and VMs.

**Cited in the paper:**
- [ ] line 70 (Introduction): "When a disaster can be forecast, the warning window can instead be used to evacuate critical data before the failure."
  - next: "To our knowledge, neither line of work models several providers with separate views that compete for the same spectrum."
- [ ] line 125 (Background and related work > Data evacuation in the warning window): "The closest line of work uses the warning itself, for example rapid data evacuation in optical cloud networks, early-warning data backup between interconnected datacenters, alert-based network reconfiguration and online evacuation of virtual machines."
  - next: "These works optimize evacuation over one network, without the competing providers and information-only cooperation of our setting."

## [19] Zhang et al. (2017). RSVP-TE Extensions for Collecting Shared Risk Link Group (SRLG) Information
*IETF RFC 8001* · key `rfc8001`  
**Link:** https://doi.org/10.17487/RFC8001 (also https://www.rfc-editor.org/rfc/rfc8001)

**Cited in the paper:**
- [ ] line 147 (Background and related work > Information disclosed by infrastructure owners): "Shared risk link group (SRLG) information can be collected along a path, although it is normally not shared with client networks."

## [20] Zou et al. (2022). DRAMA+: Disaster Management with Mitigation Awareness for Translucent Elastic Optical Networks
*IEEE Transactions on Network and Service Management* · key `zou2022dramaplus`  
**Link:** https://doi.org/10.1109/TNSM.2022.3189362

**Cited in the paper:**
- [ ] line 69 (Introduction): "Much of the work on disaster resilience in optical networks addresses restoration after the failure."
- [ ] line 119 (Background and related work > Disasters and the phases of resilience): "A common abstraction models the disaster as a zone that contains the failed nodes and links."
- [ ] line 130 (Background and related work > Post-disaster restoration in EONs): "The DRAMA family of algorithms defines a mitigation zone around the disaster zone."
  - next: "Only traffic inside the mitigation zone may be reconfigured, with degraded service, to make room for the traffic hit by the disaster, and the algorithms minimize a penalty for service degradation."
  - next: "These algorithms act after the failure; our problem takes place before it, with several providers that have local views."

## [21] Zou et al. (2021). DRAMA: Disaster Management Algorithm with Mitigation Awareness for Elastic Optical Networks
*Proc. 17th International Conference on the Design of Reliable Communication Networks (DRCN)* · key `zou2021drama`  
**Link:** https://doi.org/10.1109/DRCN51631.2021.9477320

**Cited in the paper:**
- [ ] line 69 (Introduction): "Much of the work on disaster resilience in optical networks addresses restoration after the failure."
- [ ] line 119 (Background and related work > Disasters and the phases of resilience): "A common abstraction models the disaster as a zone that contains the failed nodes and links."
- [ ] line 130 (Background and related work > Post-disaster restoration in EONs): "The DRAMA family of algorithms defines a mitigation zone around the disaster zone."
  - next: "Only traffic inside the mitigation zone may be reconfigured, with degraded service, to make room for the traffic hit by the disaster, and the algorithms minimize a penalty for service degradation."
  - next: "These algorithms act after the failure; our problem takes place before it, with several providers that have local views."

## [22] Zou et al. (2025). DRAMA-PRO+: Disaster Recovery Algorithm with Mitigation Awareness for Protected Translucent Elastic Optical Networks
*Journal of Optical Communications and Networking* · key `zou2025dramapro`  
**Link:** https://doi.org/10.1364/JOCN.561155

**Cited in the paper:**
- [ ] line 69 (Introduction): "Much of the work on disaster resilience in optical networks addresses restoration after the failure."
- [ ] line 130 (Background and related work > Post-disaster restoration in EONs): "The DRAMA family of algorithms defines a mitigation zone around the disaster zone."
  - next: "Only traffic inside the mitigation zone may be reconfigured, with degraded service, to make room for the traffic hit by the disaster, and the algorithms minimize a penalty for service degradation."
  - next: "These algorithms act after the failure; our problem takes place before it, with several providers that have local views."

