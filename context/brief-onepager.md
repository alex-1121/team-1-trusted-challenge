Source: Challenge_TRUSTED_PETs_Transformer_EN.pdf (the downloaded copy carried a ' (1)' suffix, see source-files.md) (one-page challenge sheet) from the organiser zip, converted 2026-11-06 with pdftotext. Verbatim text, only formatting added and spaced-out heading letters rejoined.

Hackathon · Technology challenge

# CHALLENGE: TrustED PETs Transformer

Protect the data, keep its value

## THE PROBLEM

Organisations often need to share, analyse or publish data, but the original data may contain personal, sensitive, confidential or otherwise restricted information. Removing names or other obvious identifiers is rarely enough: each type of data requires different protection techniques, and overly aggressive transformations can destroy the value of the dataset.

## THE CHALLENGE

Inspired by the European project TrustED (GA no. 101168467), this challenge invites teams to develop a working tool that applies Privacy-Enhancing Technologies (PETs) to sensitive datasets while preserving their analytical utility.

## THE DATA

Participants will receive one or more realistic synthetic datasets from domains such as cybersecurity, healthcare, smart cities, mobility, energy, finance, education, public administration or customer service. These datasets may include direct identifiers, quasi-identifiers, timestamps, locations, free-text fields, technical identifiers, categorical attributes, numerical measurements or aggregated statistics.

## OBJECTIVE

1. Detect or classify the types of data present
2. Select the appropriate PETs for each data type and the intended sharing scenario
3. Transform the dataset
4. Demonstrate that the protected version remains useful for a defined analytical purpose

## POSSIBLE PETS AND TRANSFORMATIONS

- Masking
- Pseudonymisation
- Tokenisation
- Generalisation
- Binning
- Suppression
- Aggregation
- Synthetic data generation
- Redaction of sensitive information in free text
- Location precision reduction
- Timestamp rounding
- Differential privacy for aggregate queries

## FINAL DEMONSTRATION

Final demonstrations must show:

1. The data types identified in the original dataset.
2. The PETs selected for each data type.
3. The transformed dataset or the protected view of the data.
4. A comparison of utility before and after the transformation.
5. A clear explanation of the sharing scenario for which the protected data is suitable.

The best solutions will not only hide sensitive values but also preserve the patterns, distributions, trends, relationships or indicators needed for the intended use case.

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101168467
