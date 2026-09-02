"""
dataset_generator/generators/report_generator.py
Generates natural-language forensic examination report text.
Multiple natural-language variations per examination type test semantic retrieval.
All reports are clearly marked as synthetic.
"""
import random
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SYNTHETIC_HEADER


# ── REPORT TEMPLATES ─────────────────────────────────────────
# Each examination type has 5+ natural-language variations.
# Variations describe similar findings in different words — critical for semantic retrieval testing.

DNA_TEMPLATES = [
    """{header}
FORENSIC DNA ANALYSIS REPORT
Report ID: {report_id} | Case: {fir} | Evidence: E{eid:03d}
Examiner: {examiner} | Laboratory: {lab} | Date: {date}

BACKGROUND:
A biological specimen was submitted for DNA profiling as part of the investigation into {fir}.

SAMPLE DESCRIPTION:
{sample_desc}

METHODOLOGY:
DNA extraction was performed using a standard organic extraction protocol. PCR amplification was conducted using the GlobalFiler kit. Capillary electrophoresis was performed on the ABI 3500XL Genetic Analyzer. Profiles were analysed using GeneMapper ID-X software.

OBSERVATIONS:
A complete 20-locus STR profile was obtained from the submitted specimen. The DNA profile was compared against the reference sample. {observation}

FINDINGS:
{finding}

CONCLUSION:
{conclusion}

LIMITATIONS:
Results are valid only for the submitted specimen. No inference is made regarding third-party involvement not within the scope of this examination.
""",

    """{header}
GENETIC PROFILE EXAMINATION REPORT
Case Reference: {fir} | Exhibit: E{eid:03d} | Lab Reference: {lab_ref}
Forensic Biologist: {examiner} | Institute: {lab} | Examination Date: {date}

EXHIBIT INFORMATION:
{sample_desc}

ANALYTICAL APPROACH:
The submitted sample underwent DNA extraction, quantification by qPCR, and short tandem repeat (STR) genotyping. Electropherogram interpretation followed standard forensic guidelines.

RESULT SUMMARY:
{observation}

FORENSIC OPINION:
{finding}

CONCLUSION:
{conclusion}

NOTE: This report constitutes the professional opinion of the signatory examiner and is subject to peer review protocols of the issuing laboratory.
""",

    """{header}
BIOLOGICAL EVIDENCE EXAMINATION — DNA TYPING REPORT
Investigation: {fir} | Evidence Reference: E{eid:03d}
Prepared by: {examiner} | Facility: {lab} | Report Date: {date}

SPECIMEN:
{sample_desc}

PROCEDURE:
STR profiling was undertaken using validated forensic DNA typing methodology. The resulting genetic profile was evaluated against reference material obtained under chain-of-custody protocols.

COMPARATIVE ANALYSIS:
{observation}

SCIENTIFIC OPINION:
{finding}

DECLARATORY CONCLUSION:
{conclusion}
""",
]

CHEMICAL_TEMPLATES = [
    """{header}
CHEMICAL COMPOSITION ANALYSIS REPORT
Case: {fir} | Evidence: E{eid:03d} | Analyst: {examiner}
Laboratory: {lab} | Date: {date}

BACKGROUND:
A substance sample was submitted for chemical characterisation.

SAMPLE:
{sample_desc}

METHODOLOGY:
Analysis was conducted using Gas Chromatography-Mass Spectrometry (GC-MS) and High Performance Liquid Chromatography (HPLC). Quantification was achieved via external standard calibration.

RESULTS:
{observation}

FORENSIC OPINION:
{finding}

CONCLUSION:
{conclusion}

LIMITATIONS:
The analysis was conducted on the submitted sample only. Homogeneity of the bulk substance is assumed but not verified.
""",

    """{header}
SUBSTANCE IDENTIFICATION & QUANTIFICATION REPORT
Reference: {fir} | Exhibit No: E{eid:03d}
Chemist: {examiner} | FSL: {lab} | Dated: {date}

EXHIBIT:
{sample_desc}

TECHNIQUE:
GC-MS profiling with NIST library matching. Purity determined by area normalisation method.

ANALYTICAL FINDINGS:
{observation}

OPINION:
{finding}

CONCLUSION:
{conclusion}
""",

    """{header}
NARCOTICS/CONTROLLED SUBSTANCE EXAMINATION
Investigation No: {fir} | Item: E{eid:03d}
Forensic Chemist: {examiner} | Issuing Lab: {lab} | Report Date: {date}

DESCRIPTION OF SUBMITTED MATERIAL:
{sample_desc}

EXAMINATION METHODOLOGY:
Colour spot tests (Scott, Marquis, Mecke) applied as preliminary screening. Confirmatory analysis by GC-MS. Purity calculated against certified reference standards.

FINDINGS:
{observation}

FORENSIC INTERPRETATION:
{finding}

DECLARATORY STATEMENT:
{conclusion}
""",
]

DIGITAL_TEMPLATES = [
    """{header}
DIGITAL FORENSIC EXAMINATION REPORT
Case: {fir} | Exhibit: E{eid:03d} | Examiner: {examiner}
Laboratory: {lab} | Examination Date: {date}

BACKGROUND:
A digital device was submitted for forensic examination in connection with {fir}.

EXHIBIT DESCRIPTION:
{sample_desc}

METHODOLOGY:
A forensic image was created using a write-blocking device. Acquisition hash verified. Examination conducted using Autopsy, FTK Imager, and Cellebrite UFED where applicable.

FINDINGS:
{observation}

FORENSIC OPINION:
{finding}

CONCLUSION:
{conclusion}

LIMITATIONS:
Encryption and anti-forensics measures may have restricted access to certain data.
""",

    """{header}
CYBER FORENSICS TECHNICAL REPORT
Investigation: {fir} | Exhibit Reference: E{eid:03d}
Digital Forensics Analyst: {examiner} | Unit: {lab} | Date: {date}

DEVICE INFORMATION:
{sample_desc}

ACQUISITION:
Bit-for-bit forensic copy created under write-block conditions. MD5 and SHA-256 acquisition hashes verified.

EXAMINATION RESULTS:
{observation}

TECHNICAL OPINION:
{finding}

SUMMARY:
{conclusion}
""",
]

FINGERPRINT_TEMPLATES = [
    """{header}
FINGERPRINT COMPARISON EXAMINATION REPORT
Case Reference: {fir} | Evidence: E{eid:03d}
Fingerprint Expert: {examiner} | Laboratory: {lab} | Date: {date}

EXHIBIT:
{sample_desc}

METHODOLOGY:
Latent prints were developed using fluorescent powder/ninhydrin/DFO where appropriate. Developed prints were photographed and compared against ten-print reference cards using the ACE-V methodology (Analysis, Comparison, Evaluation, Verification).

FINDINGS:
{observation}

EXPERT OPINION:
{finding}

CONCLUSION:
{conclusion}
""",

    """{header}
LATENT PRINT ANALYSIS REPORT
Investigation No: {fir} | Item: E{eid:03d}
Examiner: {examiner} | Forensic Unit: {lab} | Report Date: {date}

SUBMITTED MATERIAL:
{sample_desc}

EXAMINATION:
Latent impressions were subjected to AFIS (Automated Fingerprint Identification System) database search and manual ACE-V comparison.

RESULT:
{observation}

DECLARATION:
{finding}

CONCLUSION:
{conclusion}
""",
]

BALLISTICS_TEMPLATES = [
    """{header}
BALLISTICS AND FIREARMS EXAMINATION REPORT
Case: {fir} | Evidence: E{eid:03d} | Examiner: {examiner}
Laboratory: {lab} | Date: {date}

SUBMITTED ITEMS:
{sample_desc}

METHODOLOGY:
Firearm function testing, rifling examination, cartridge case comparison, and gunshot residue (GSR) analysis were conducted as applicable. Comparison microscopy used for striation analysis.

FINDINGS:
{observation}

FORENSIC OPINION:
{finding}

CONCLUSION:
{conclusion}
""",
]

SEROLOGY_TEMPLATES = [
    """{header}
SEROLOGY EXAMINATION REPORT
Case Reference: {fir} | Exhibit: E{eid:03d}
Serologist: {examiner} | Laboratory: {lab} | Date: {date}

EXHIBIT INFORMATION:
{sample_desc}

METHODOLOGY:
Presumptive testing (Kastle-Meyer/Luminol) followed by confirmatory serology (Ouchterlony). ABO blood typing by agglutination.

FINDINGS:
{observation}

FORENSIC OPINION:
{finding}

CONCLUSION:
{conclusion}
""",
]

# Map ExaminationType.type_id → template list
TEMPLATES_BY_TYPE = {
    1: DNA_TEMPLATES,
    2: CHEMICAL_TEMPLATES,
    3: DIGITAL_TEMPLATES,
    4: FINGERPRINT_TEMPLATES,
    5: BALLISTICS_TEMPLATES,
    6: SEROLOGY_TEMPLATES,
}

# ── OBSERVATION / FINDING / CONCLUSION VARIANTS ──────────────

DNA_OBSERVATIONS = [
    "The genetic profile obtained from the specimen was consistent with the reference profile.",
    "DNA profiling revealed a correspondence between the questioned sample and the reference material.",
    "Analysis of the biological specimen produced a matching DNA profile.",
    "The STR profile from the evidence item matched the reference sample at all 20 loci tested.",
    "Comparative analysis of the DNA profile confirmed a full concordance with the submitted reference.",
    "No match was established between the queried specimen and the reference sample.",
    "A partial DNA profile was obtained — insufficient for conclusive comparison.",
    "The DNA profile obtained was consistent with a mixture of at least two contributors.",
]

DNA_FINDINGS = [
    "The DNA profile from the specimen is consistent with originating from the reference individual.",
    "The genetic evidence supports the association between the questioned sample and the reference donor.",
    "Based on statistical analysis (RMP: 1 in >1 billion), the evidence supports common origin.",
    "The evidence is consistent with contamination or mixture — single-source attribution is not possible.",
    "The partial profile cannot be used for conclusive identification.",
]

DNA_CONCLUSIONS = [
    "The submitted biological specimen is consistent with originating from the reference individual. The evidence is admissible.",
    "DNA analysis supports a match between the specimen and the reference sample. Result: MATCH.",
    "No correspondence was established. The specimen is EXCLUDED as originating from the reference individual.",
    "Inconclusive result — mixture or degradation prevents single-source attribution.",
]

CHEMICAL_OBSERVATIONS = [
    "The substance was identified as diacetylmorphine (heroin) with purity {purity}%.",
    "GC-MS analysis confirmed the presence of cocaine hydrochloride at {purity}% purity.",
    "The examined material tested positive for methamphetamine ({purity}% by weight).",
    "MDMA (3,4-methylenedioxymethamphetamine) was detected at {purity}% concentration.",
    "The substance is consistent with cannabis resin (hashish). No adulterants detected.",
    "The sample was identified as a non-controlled pharmaceutical substance. No scheduled drugs present.",
]

CHEMICAL_FINDINGS = [
    "The substance constitutes a controlled drug under the NDPS Act, Schedule I.",
    "The identified compound is a Class A controlled substance under applicable narcotic laws.",
    "No controlled substance was identified. The material is not a scheduled drug.",
]

CHEMICAL_CONCLUSIONS = [
    "The submitted substance is confirmed as {drug} at {purity}% purity. Total net weight (corrected): {weight}g. This is a controlled substance under NDPS Act.",
    "Chemical analysis confirms the presence of {drug}. The substance is a narcotic/psychotropic substance under Schedule {schedule}.",
    "No scheduled drug identified. The substance does not constitute a controlled material.",
]

DIGITAL_OBSERVATIONS = [
    "Examination of the device revealed deleted files recovered from unallocated space.",
    "Encrypted volumes were identified. Partial decryption was achieved using known-key methodology.",
    "Network artefacts including browser history, email communications, and chat logs were extracted.",
    "No relevant digital artefacts were found on the submitted device.",
    "Financial transaction records, fraudulent account details, and victim data were recovered.",
    "The device contained {count} images/videos relevant to the investigation.",
]

DIGITAL_FINDINGS = [
    "The recovered data is consistent with the alleged offence.",
    "Deleted communications corroborate the suspected fraudulent activity.",
    "No incriminating digital evidence was identified on the submitted device.",
]

DIGITAL_CONCLUSIONS = [
    "The digital device contained evidence relevant to the investigation. Extracted data is admissible subject to chain-of-custody verification.",
    "No digital evidence of relevance to the case was recovered.",
    "Partial evidence recovered — encrypted or deleted data may have been irretrievably lost.",
]

FINGERPRINT_OBSERVATIONS = [
    "{count} distinct fingerprint sets were identified on the examined exhibit.",
    "Latent prints matched the reference card of {name} with {confidence}% confidence (AFIS).",
    "No suitable latent prints were recovered from the submitted item.",
    "Prints recovered were of insufficient quality for comparative analysis.",
    "The AFIS database search returned no candidate match.",
]

FINGERPRINT_FINDINGS = [
    "The latent print is identified as having been made by {name}.",
    "The recovered print cannot be attributed to any identified individual.",
    "Insufficient ridge detail prevents conclusive comparison.",
]

FINGERPRINT_CONCLUSIONS = [
    "Fingerprint analysis establishes that {name} handled the submitted exhibit. Evidence is admissible.",
    "No identifiable fingerprints recovered. Negative result — does not exclude suspect involvement.",
    "Inconclusive — ridge quality insufficient for comparison.",
]

FINDINGS_BY_TYPE = {
    1: (DNA_OBSERVATIONS,        DNA_FINDINGS,        DNA_CONCLUSIONS),
    2: (CHEMICAL_OBSERVATIONS,   CHEMICAL_FINDINGS,   CHEMICAL_CONCLUSIONS),
    3: (DIGITAL_OBSERVATIONS,    DIGITAL_FINDINGS,    DIGITAL_CONCLUSIONS),
    4: (FINGERPRINT_OBSERVATIONS,FINGERPRINT_FINDINGS,FINGERPRINT_CONCLUSIONS),
    5: (FINGERPRINT_OBSERVATIONS,FINGERPRINT_FINDINGS,FINGERPRINT_CONCLUSIONS),   # reuse for ballistics
    6: (DNA_OBSERVATIONS,        DNA_FINDINGS,        DNA_CONCLUSIONS),            # reuse for serology
}

SAMPLE_DESCRIPTIONS = {
    1: ["Blood sample sealed in sterile container", "Tissue swab from crime scene surface",
        "DNA swab collected from suspect item", "Saliva sample on cotton swab"],
    2: ["White crystalline powder sealed in evidence bag",
        "Brown granular substance in polythene pouch",
        "Liquid substance in sealed glass vial",
        "Tablet residue collected from exhibit"],
    3: ["Laptop computer in anti-static evidence bag",
        "Mobile phone sealed in Faraday cage",
        "USB storage device with tamper-evident seal",
        "Hard drive removed from seized computer"],
    4: ["Surface swab submitted for latent print development",
        "Exhibit with visible friction ridge impressions",
        "Glass surface with latent impressions"],
    5: ["Firearm with cartridge cases",
        "Bullet recovered from crime scene",
        "Cartridge cases collected from scene"],
    6: ["Blood-stained fabric submitted for typing",
        "Bloodstain on surface for ABO typing"],
}


class ReportGenerator:
    """Generates natural-language forensic examination report text."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self._fake_name = lambda: random.choice([
            "Arvind Sharma", "Meena Krishnan", "Rajiv Patel",
            "Sunita Mehta", "Kiran Deshmukh", "Anita Roy",
        ])

    def generate_report_text(
        self, exam_type_id: int, fir: str, evidence_id: int,
        examiner_name: str, lab_name: str, exam_date: str,
        report_id: str = "RPT-SYN", lab_ref: str = None
    ) -> str:
        templates = TEMPLATES_BY_TYPE.get(exam_type_id, DNA_TEMPLATES)
        tmpl = random.choice(templates)

        obs_list, find_list, conc_list = FINDINGS_BY_TYPE.get(
            exam_type_id, (DNA_OBSERVATIONS, DNA_FINDINGS, DNA_CONCLUSIONS)
        )
        sample_list = SAMPLE_DESCRIPTIONS.get(exam_type_id, ["Evidence item submitted for analysis"])

        observation = random.choice(obs_list).format(
            count      = random.randint(1, 5),
            name       = self._fake_name(),
            confidence = random.randint(85, 99),
            purity     = round(random.uniform(60.0, 99.9), 1),
        )
        finding = random.choice(find_list).format(
            name = self._fake_name(),
        )
        conclusion = random.choice(conc_list).format(
            drug     = random.choice(["heroin", "cocaine", "methamphetamine", "MDMA"]),
            purity   = round(random.uniform(60.0, 99.9), 1),
            weight   = round(random.uniform(10.0, 5000.0), 1),
            schedule = random.choice(["I", "II"]),
            name     = self._fake_name(),
        )

        return tmpl.format(
            header      = SYNTHETIC_HEADER,
            report_id   = report_id,
            fir         = fir,
            eid         = evidence_id,
            examiner    = examiner_name,
            lab         = lab_name,
            lab_ref     = lab_ref or f"LAB-{random.randint(10000, 99999)}",
            date        = exam_date,
            sample_desc = random.choice(sample_list),
            observation = observation,
            finding     = finding,
            conclusion  = conclusion,
        )
