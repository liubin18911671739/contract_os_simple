/**
 * Contracts API
 */
import { get, post, uploadFile } from './http';

export interface Contract {
  id: string;
  contract_name: string;
  counterparty?: string;
  contract_type?: string;
  created_at: string;
  versions: ContractVersion[];
}

export interface ContractVersion {
  id: string;
  version_no: number;
  mime: string;
  sha256: string;
  created_at: string;
}

export async function createContract(data: {
  contract_name: string;
  counterparty?: string;
  contract_type?: string;
}): Promise<{ id: string }> {
  return post('/contracts', data);
}

export async function uploadContractVersion(
  contractId: string,
  file: File
): Promise<ContractVersion> {
  return uploadFile(`/contracts/${contractId}/versions`, file);
}

export async function getContract(contractId: string): Promise<Contract> {
  return get(`/contracts/${contractId}`);
}
