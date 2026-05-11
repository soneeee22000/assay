// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import { Script, console2 } from "forge-std/Script.sol";
import { GemVaultCertificate } from "../src/GemVaultCertificate.sol";

contract Deploy is Script {
    function run() external returns (GemVaultCertificate cert) {
        uint256 deployerKey = vm.envUint("ADMIN_PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        vm.startBroadcast(deployerKey);
        cert = new GemVaultCertificate(deployer);
        vm.stopBroadcast();

        console2.log("GemVaultCertificate deployed at:", address(cert));
        console2.log("Admin:", deployer);
    }
}
