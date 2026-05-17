// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Script, console2} from "forge-std/Script.sol";
import {AssayCertificate} from "../src/AssayCertificate.sol";

contract Deploy is Script {
    function run() external returns (AssayCertificate cert) {
        uint256 deployerKey = vm.envUint("ADMIN_PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        vm.startBroadcast(deployerKey);
        cert = new AssayCertificate(deployer);
        vm.stopBroadcast();

        console2.log("AssayCertificate deployed at:", address(cert));
        console2.log("Admin:", deployer);
    }
}
