// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {AssayCertificate} from "../src/AssayCertificate.sol";

contract AssayCertificateTest is Test {
    AssayCertificate internal cert;
    address internal admin = address(0xA11CE);
    address internal alice = address(0xA1);
    address internal bob = address(0xB0B);

    string internal constant IPFS_HASH = "QmTestHash";
    string internal constant VAULT_REF = "ZUR-2026-05-11-A47C";

    function setUp() public {
        vm.prank(admin);
        cert = new AssayCertificate(admin);
    }

    function test_admin_can_mint_to_user() public {
        vm.prank(admin);
        cert.mint(alice, 1, IPFS_HASH);

        assertEq(cert.ownerOf(1), alice);
        assertEq(cert.tokenURI(1), string.concat("ipfs://", IPFS_HASH));
    }

    function test_mint_reverts_for_non_minter() public {
        vm.expectRevert();
        vm.prank(alice);
        cert.mint(alice, 1, IPFS_HASH);
    }

    function test_transfer_reverts_without_attestation() public {
        vm.prank(admin);
        cert.mint(alice, 1, IPFS_HASH);

        vm.expectRevert(
            abi.encodeWithSelector(AssayCertificate.TransferRequiresVaultAttestation.selector, 1)
        );
        vm.prank(alice);
        cert.transferFrom(alice, bob, 1);
    }

    function test_transfer_succeeds_after_attestation() public {
        vm.startPrank(admin);
        cert.mint(alice, 1, IPFS_HASH);
        cert.attestVault(1, VAULT_REF);
        vm.stopPrank();

        vm.prank(alice);
        cert.transferFrom(alice, bob, 1);

        assertEq(cert.ownerOf(1), bob);
    }

    function test_attest_reverts_for_non_attester() public {
        vm.prank(admin);
        cert.mint(alice, 1, IPFS_HASH);

        vm.expectRevert();
        vm.prank(alice);
        cert.attestVault(1, VAULT_REF);
    }

    function test_double_attestation_reverts() public {
        vm.startPrank(admin);
        cert.mint(alice, 1, IPFS_HASH);
        cert.attestVault(1, VAULT_REF);

        vm.expectRevert(abi.encodeWithSelector(AssayCertificate.AlreadyAttested.selector, 1));
        cert.attestVault(1, VAULT_REF);
        vm.stopPrank();
    }

    function test_pause_blocks_minting_and_transfer() public {
        vm.startPrank(admin);
        cert.mint(alice, 1, IPFS_HASH);
        cert.attestVault(1, VAULT_REF);
        cert.pause();

        vm.expectRevert();
        cert.mint(alice, 2, IPFS_HASH);
        vm.stopPrank();

        vm.expectRevert();
        vm.prank(alice);
        cert.transferFrom(alice, bob, 1);
    }
}
