#!/usr/bin/env python3
"""
Seed script to create sample KB collections and documents
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from server.database.connection import get_session_maker, init_db
from server.services.kb_service import KBService


async def main():
    """Seed KB with sample data"""
    print("Checking database...")

    session_maker = get_session_maker()

    async with session_maker() as session:
        kb_service = KBService(session)

        # Check if collections already exist
        existing_collections = await kb_service.list_collections()
        existing_names = {col["name"] for col in existing_collections}

        # Create sample collections
        print("\nCreating KB collections...")

        # Contract regulations collection
        if "Contract Regulations" in existing_names:
            # Get existing collection
            reg_col_id = next(col["id"] for col in existing_collections if col["name"] == "Contract Regulations")
            print(f"✓ Already exists: Contract Regulations ({reg_col_id})")
        else:
            reg_col_id = await kb_service.create_collection(
                name="Contract Regulations",
                scope="GLOBAL"
            )
            print(f"✓ Created: Contract Regulations ({reg_col_id})")

        # Best practices collection
        if "Contract Best Practices" in existing_names:
            bp_col_id = next(col["id"] for col in existing_collections if col["name"] == "Contract Best Practices")
            print(f"✓ Already exists: Contract Best Practices ({bp_col_id})")
        else:
            bp_col_id = await kb_service.create_collection(
                name="Contract Best Practices",
                scope="GLOBAL"
            )
            print(f"✓ Created: Contract Best Practices ({bp_col_id})")

        # Create sample documents
        print("\nImporting sample documents...")
        print("Note: If API quota is exceeded, collections will be created without embeddings.")

        try:
            # Create a sample regulation document
            sample_reg_path = Path(__file__).parent / "sample_regulation.txt"
            sample_reg_path.write_text("""
# Contract Risk Regulations

## 1. Liability Limitations

Contracts should always include liability limitations. Unlimited liability clauses pose significant risks to both parties.

### Key Points:
- Liability should be capped at contract value or a multiple thereof
- Consequential damages should be excluded
- No liability for indirect or punitive damages

## 2. Termination Rights

Fair termination provisions are essential for contract flexibility.

### Best Practices:
- Allow termination for cause with notice period
- Include termination for convenience with reasonable fees
- Define cure periods for breaches

## 3. Payment Terms

Clear payment terms prevent disputes and cash flow issues.

### Recommendations:
- Specify payment due dates clearly
- Include late payment penalties
- Define payment methods and currency

## 4. Confidentiality

Protect sensitive information with proper confidentiality clauses.

### Required Elements:
- Define what constitutes confidential information
- Specify permitted uses and disclosure
- Set duration of confidentiality obligations

## 5. Dispute Resolution

Efficient dispute resolution saves time and costs.

### Options to Consider:
- Mediation as first step
- Arbitration clauses with specified rules
- Governing law and jurisdiction
            """.strip())

            await kb_service.import_document(
                collection_id=reg_col_id,
                title="General Contract Risk Regulations",
                doc_type="regulation",
                file_path=str(sample_reg_path),
            )
            print(f"✓ Imported: General Contract Risk Regulations")

            # Create a sample best practices document
            sample_bp_path = Path(__file__).parent / "sample_practices.txt"
            sample_bp_path.write_text("""
# Contract Review Best Practices

## Risk Assessment Framework

When reviewing contracts, assess risks in three categories:

### HIGH Risk Items
- Unlimited liability clauses
- Unfair termination provisions
- Automatic renewal without notice
- Unclear payment terms
- Missing dispute resolution

### MEDIUM Risk Items
- Long notice periods
- Restrictive confidentiality terms
- One-sided indemnification
- Vague deliverables

### LOW Risk Items
- Minor administrative provisions
- Standard boilerplate language
- Non-material terms

## Review Checklist

Before signing, ensure:
1. All parties are correctly identified
2. Scope of work is clearly defined
3. Payment terms are complete and clear
4. Liability is appropriately limited
5. Termination rights are balanced
6. Confidentiality obligations are reasonable
7. Dispute resolution is specified
8. Governing law is appropriate

## Red Flags

Watch out for:
- "Time is of the essence" without justification
- Blank spaces for future terms
- References to undefined documents
- Unilateral modification rights
- Waivers of legal rights
            """.strip())

            await kb_service.import_document(
                collection_id=bp_col_id,
                title="Contract Review Best Practices",
                doc_type="guideline",
                file_path=str(sample_bp_path),
            )
            print(f"✓ Imported: Contract Review Best Practices")

            print("\n✓ KB seeding complete!")
            print(f"\nCollection IDs:")
            print(f"  - Regulations: {reg_col_id}")
            print(f"  - Best Practices: {bp_col_id}")

        except Exception as e:
            print(f"\n⚠ Warning: Could not import documents (API quota exceeded?)")
            print(f"  Error: {str(e)}")
            print(f"\n  Collections created successfully:")
            print(f"  - Regulations: {reg_col_id}")
            print(f"  - Best Practices: {bp_col_id}")
            print(f"\n  You can import documents later via the API or UI.")
            return


if __name__ == "__main__":
    asyncio.run(main())
