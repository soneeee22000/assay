// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/utils/Pausable.sol";

/// @title GemVaultCertificate
/// @notice ERC-721 certificate of authenticity for physical assets. Transfers are
///         gated behind an off-chain vault attestation (recorded on-chain by the
///         platform's ATTESTER_ROLE). See docs/adr/decisions.md ADR-002.
contract GemVaultCertificate is ERC721, AccessControl, Pausable {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ATTESTER_ROLE = keccak256("ATTESTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    struct Attestation {
        bool attested;
        string vaultRef;
        uint256 attestedAt;
    }

    mapping(uint256 tokenId => string ipfsHash) private _ipfsMetadataHash;
    mapping(uint256 tokenId => Attestation attestation) public attestations;

    event CertificateMinted(uint256 indexed tokenId, address indexed to, string ipfsHash);
    event VaultAttested(uint256 indexed tokenId, string vaultRef, uint256 attestedAt);

    error TransferRequiresVaultAttestation(uint256 tokenId);
    error TokenDoesNotExist(uint256 tokenId);
    error AlreadyAttested(uint256 tokenId);

    constructor(address admin) ERC721("GemVault Certificate", "GVC") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(ATTESTER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    function mint(address to, uint256 tokenId, string calldata ipfsHash)
        external
        onlyRole(MINTER_ROLE)
        whenNotPaused
    {
        _safeMint(to, tokenId);
        _ipfsMetadataHash[tokenId] = ipfsHash;
        emit CertificateMinted(tokenId, to, ipfsHash);
    }

    function attestVault(uint256 tokenId, string calldata vaultRef)
        external
        onlyRole(ATTESTER_ROLE)
    {
        if (_ownerOf(tokenId) == address(0)) {
            revert TokenDoesNotExist(tokenId);
        }
        if (attestations[tokenId].attested) {
            revert AlreadyAttested(tokenId);
        }

        attestations[tokenId] =
            Attestation({attested: true, vaultRef: vaultRef, attestedAt: block.timestamp});
        emit VaultAttested(tokenId, vaultRef, block.timestamp);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        if (_ownerOf(tokenId) == address(0)) {
            revert TokenDoesNotExist(tokenId);
        }
        return string.concat("ipfs://", _ipfsMetadataHash[tokenId]);
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        whenNotPaused
        returns (address)
    {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) {
            if (!attestations[tokenId].attested) {
                revert TransferRequiresVaultAttestation(tokenId);
            }
        }
        return super._update(to, tokenId, auth);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
