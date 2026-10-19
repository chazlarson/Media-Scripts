#!/usr/bin/env python3
"""Generate a minimal iOS Xcode project for Corner Empire / IdleTycoon."""

from __future__ import annotations

import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "IdleTycoon.xcodeproj"
SOURCES = [
    "IdleTycoon/IdleTycoonApp.swift",
    "IdleTycoon/Models/Business.swift",
    "IdleTycoon/Models/GameSave.swift",
    "IdleTycoon/Services/Economy.swift",
    "IdleTycoon/Services/GameStore.swift",
    "IdleTycoon/ViewModels/GameViewModel.swift",
    "IdleTycoon/Views/Theme.swift",
    "IdleTycoon/Views/BusinessRowView.swift",
    "IdleTycoon/Views/ContentView.swift",
]
TESTS = [
    "IdleTycoonTests/EconomyTests.swift",
]
ASSETS = "IdleTycoon/Assets.xcassets"


def uid() -> str:
    return uuid.uuid4().hex[:24].upper()


def main() -> None:
    ids = {
        "project": uid(),
        "app_target": uid(),
        "test_target": uid(),
        "sources_phase": uid(),
        "resources_phase": uid(),
        "frameworks_phase": uid(),
        "test_sources_phase": uid(),
        "test_frameworks_phase": uid(),
        "app_product": uid(),
        "test_product": uid(),
        "app_config_list": uid(),
        "test_config_list": uid(),
        "project_config_list": uid(),
        "debug_project": uid(),
        "release_project": uid(),
        "debug_app": uid(),
        "release_app": uid(),
        "debug_test": uid(),
        "release_test": uid(),
        "group_root": uid(),
        "group_app": uid(),
        "group_models": uid(),
        "group_services": uid(),
        "group_viewmodels": uid(),
        "group_views": uid(),
        "group_tests": uid(),
        "group_products": uid(),
        "assets": uid(),
        "test_dependency": uid(),
        "test_container": uid(),
    }

    file_ids = {path: uid() for path in SOURCES + TESTS}
    build_ids = {path: uid() for path in SOURCES + TESTS}
    assets_build = uid()

    def build_file(path: str) -> str:
        return (
            f"\t\t{build_ids[path]} /* {Path(path).name} in Sources */ = "
            f"{{isa = PBXBuildFile; fileRef = {file_ids[path]} /* {Path(path).name} */; }};"
        )

    def file_ref(path: str) -> str:
        return (
            f"\t\t{file_ids[path]} /* {Path(path).name} */ = "
            f"{{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; "
            f"path = {Path(path).name}; sourceTree = \"<group>\"; }};"
        )

    lines: list[str] = []
    lines.append("// !$*UTF8*$!")
    lines.append("{")
    lines.append("\tarchiveVersion = 1;")
    lines.append("\tclasses = {")
    lines.append("\t};")
    lines.append("\tobjectVersion = 56;")
    lines.append("\tobjects = {")
    lines.append("")
    lines.append("/* Begin PBXBuildFile section */")
    for path in SOURCES:
        lines.append(build_file(path))
    for path in TESTS:
        lines.append(build_file(path))
    lines.append(
        f"\t\t{assets_build} /* Assets.xcassets in Resources */ = "
        f"{{isa = PBXBuildFile; fileRef = {ids['assets']} /* Assets.xcassets */; }};"
    )
    lines.append("/* End PBXBuildFile section */")
    lines.append("")
    lines.append("/* Begin PBXFileReference section */")
    lines.append(
        f"\t\t{ids['app_product']} /* IdleTycoon.app */ = "
        "{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; "
        "path = IdleTycoon.app; sourceTree = BUILT_PRODUCTS_DIR; };"
    )
    lines.append(
        f"\t\t{ids['test_product']} /* IdleTycoonTests.xctest */ = "
        "{isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; "
        "path = IdleTycoonTests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };"
    )
    for path in SOURCES + TESTS:
        lines.append(file_ref(path))
    lines.append(
        f"\t\t{ids['assets']} /* Assets.xcassets */ = "
        "{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; "
        "path = Assets.xcassets; sourceTree = \"<group>\"; };"
    )
    lines.append("/* End PBXFileReference section */")
    lines.append("")
    lines.append("/* Begin PBXFrameworksBuildPhase section */")
    lines.append(f"\t\t{ids['frameworks_phase']} /* Frameworks */ = {{")
    lines.append("\t\t\tisa = PBXFrameworksBuildPhase;")
    lines.append("\t\t\tbuildActionMask = 2147483647;")
    lines.append("\t\t\tfiles = (")
    lines.append("\t\t\t);")
    lines.append("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['test_frameworks_phase']} /* Frameworks */ = {{")
    lines.append("\t\t\tisa = PBXFrameworksBuildPhase;")
    lines.append("\t\t\tbuildActionMask = 2147483647;")
    lines.append("\t\t\tfiles = (")
    lines.append("\t\t\t);")
    lines.append("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    lines.append("\t\t};")
    lines.append("/* End PBXFrameworksBuildPhase section */")
    lines.append("")
    lines.append("/* Begin PBXGroup section */")
    lines.append(f"\t\t{ids['group_root']} = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    lines.append(f"\t\t\t\t{ids['group_app']} /* IdleTycoon */,")
    lines.append(f"\t\t\t\t{ids['group_tests']} /* IdleTycoonTests */,")
    lines.append(f"\t\t\t\t{ids['group_products']} /* Products */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_products']} /* Products */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    lines.append(f"\t\t\t\t{ids['app_product']} /* IdleTycoon.app */,")
    lines.append(f"\t\t\t\t{ids['test_product']} /* IdleTycoonTests.xctest */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tname = Products;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_app']} /* IdleTycoon */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    lines.append(f"\t\t\t\t{file_ids['IdleTycoon/IdleTycoonApp.swift']} /* IdleTycoonApp.swift */,")
    lines.append(f"\t\t\t\t{ids['group_models']} /* Models */,")
    lines.append(f"\t\t\t\t{ids['group_services']} /* Services */,")
    lines.append(f"\t\t\t\t{ids['group_viewmodels']} /* ViewModels */,")
    lines.append(f"\t\t\t\t{ids['group_views']} /* Views */,")
    lines.append(f"\t\t\t\t{ids['assets']} /* Assets.xcassets */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = IdleTycoon;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_models']} /* Models */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    for path in [p for p in SOURCES if "/Models/" in p]:
        lines.append(f"\t\t\t\t{file_ids[path]} /* {Path(path).name} */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = Models;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_services']} /* Services */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    for path in [p for p in SOURCES if "/Services/" in p]:
        lines.append(f"\t\t\t\t{file_ids[path]} /* {Path(path).name} */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = Services;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_viewmodels']} /* ViewModels */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    for path in [p for p in SOURCES if "/ViewModels/" in p]:
        lines.append(f"\t\t\t\t{file_ids[path]} /* {Path(path).name} */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = ViewModels;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_views']} /* Views */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    for path in [p for p in SOURCES if "/Views/" in p]:
        lines.append(f"\t\t\t\t{file_ids[path]} /* {Path(path).name} */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = Views;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['group_tests']} /* IdleTycoonTests */ = {{")
    lines.append("\t\t\tisa = PBXGroup;")
    lines.append("\t\t\tchildren = (")
    for path in TESTS:
        lines.append(f"\t\t\t\t{file_ids[path]} /* {Path(path).name} */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tpath = IdleTycoonTests;")
    lines.append("\t\t\tsourceTree = \"<group>\";")
    lines.append("\t\t};")
    lines.append("/* End PBXGroup section */")
    lines.append("")
    lines.append("/* Begin PBXNativeTarget section */")
    lines.append(f"\t\t{ids['app_target']} /* IdleTycoon */ = {{")
    lines.append("\t\t\tisa = PBXNativeTarget;")
    lines.append("\t\t\tbuildConfigurationList = "
                 f"{ids['app_config_list']} /* Build configuration list for PBXNativeTarget \"IdleTycoon\" */;")
    lines.append("\t\t\tbuildPhases = (")
    lines.append(f"\t\t\t\t{ids['sources_phase']} /* Sources */,")
    lines.append(f"\t\t\t\t{ids['frameworks_phase']} /* Frameworks */,")
    lines.append(f"\t\t\t\t{ids['resources_phase']} /* Resources */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tbuildRules = (")
    lines.append("\t\t\t);")
    lines.append("\t\t\tdependencies = (")
    lines.append("\t\t\t);")
    lines.append("\t\t\tname = IdleTycoon;")
    lines.append("\t\t\tproductName = IdleTycoon;")
    lines.append(f"\t\t\tproductReference = {ids['app_product']} /* IdleTycoon.app */;")
    lines.append("\t\t\tproductType = \"com.apple.product-type.application\";")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['test_target']} /* IdleTycoonTests */ = {{")
    lines.append("\t\t\tisa = PBXNativeTarget;")
    lines.append("\t\t\tbuildConfigurationList = "
                 f"{ids['test_config_list']} /* Build configuration list for PBXNativeTarget \"IdleTycoonTests\" */;")
    lines.append("\t\t\tbuildPhases = (")
    lines.append(f"\t\t\t\t{ids['test_sources_phase']} /* Sources */,")
    lines.append(f"\t\t\t\t{ids['test_frameworks_phase']} /* Frameworks */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tbuildRules = (")
    lines.append("\t\t\t);")
    lines.append("\t\t\tdependencies = (")
    lines.append(f"\t\t\t\t{ids['test_dependency']} /* PBXTargetDependency */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tname = IdleTycoonTests;")
    lines.append("\t\t\tproductName = IdleTycoonTests;")
    lines.append(f"\t\t\tproductReference = {ids['test_product']} /* IdleTycoonTests.xctest */;")
    lines.append("\t\t\tproductType = \"com.apple.product-type.bundle.unit-test\";")
    lines.append("\t\t};")
    lines.append("/* End PBXNativeTarget section */")
    lines.append("")
    lines.append("/* Begin PBXContainerItemProxy section */")
    lines.append(f"\t\t{ids['test_container']} /* PBXContainerItemProxy */ = {{")
    lines.append("\t\t\tisa = PBXContainerItemProxy;")
    lines.append(f"\t\t\tcontainerPortal = {ids['project']} /* Project object */;")
    lines.append("\t\t\tproxyType = 1;")
    lines.append(f"\t\t\tremoteGlobalIDString = {ids['app_target']};")
    lines.append("\t\t\tremoteInfo = IdleTycoon;")
    lines.append("\t\t};")
    lines.append("/* End PBXContainerItemProxy section */")
    lines.append("")
    lines.append("/* Begin PBXTargetDependency section */")
    lines.append(f"\t\t{ids['test_dependency']} /* PBXTargetDependency */ = {{")
    lines.append("\t\t\tisa = PBXTargetDependency;")
    lines.append(f"\t\t\ttarget = {ids['app_target']} /* IdleTycoon */;")
    lines.append(f"\t\t\ttargetProxy = {ids['test_container']} /* PBXContainerItemProxy */;")
    lines.append("\t\t};")
    lines.append("/* End PBXTargetDependency section */")
    lines.append("")
    lines.append("/* Begin PBXProject section */")
    lines.append(f"\t\t{ids['project']} /* Project object */ = {{")
    lines.append("\t\t\tisa = PBXProject;")
    lines.append("\t\t\tattributes = {")
    lines.append("\t\t\t\tBuildIndependentTargetsInParallel = 1;")
    lines.append("\t\t\t\tLastSwiftUpdateCheck = 1600;")
    lines.append("\t\t\t\tLastUpgradeCheck = 1600;")
    lines.append("\t\t\t};")
    lines.append("\t\t\tbuildConfigurationList = "
                 f"{ids['project_config_list']} /* Build configuration list for PBXProject \"IdleTycoon\" */;")
    lines.append("\t\t\tcompatibilityVersion = \"Xcode 14.0\";")
    lines.append("\t\t\tdevelopmentRegion = en;")
    lines.append("\t\t\thasScannedForEncodings = 0;")
    lines.append("\t\t\tknownRegions = (")
    lines.append("\t\t\t\ten,")
    lines.append("\t\t\t\tBase,")
    lines.append("\t\t\t);")
    lines.append(f"\t\t\tmainGroup = {ids['group_root']};")
    lines.append(f"\t\t\tproductRefGroup = {ids['group_products']} /* Products */;")
    lines.append("\t\t\tprojectDirPath = \"\";")
    lines.append("\t\t\tprojectRoot = \"\";")
    lines.append("\t\t\ttargets = (")
    lines.append(f"\t\t\t\t{ids['app_target']} /* IdleTycoon */,")
    lines.append(f"\t\t\t\t{ids['test_target']} /* IdleTycoonTests */,")
    lines.append("\t\t\t);")
    lines.append("\t\t};")
    lines.append("/* End PBXProject section */")
    lines.append("")
    lines.append("/* Begin PBXResourcesBuildPhase section */")
    lines.append(f"\t\t{ids['resources_phase']} /* Resources */ = {{")
    lines.append("\t\t\tisa = PBXResourcesBuildPhase;")
    lines.append("\t\t\tbuildActionMask = 2147483647;")
    lines.append("\t\t\tfiles = (")
    lines.append(f"\t\t\t\t{assets_build} /* Assets.xcassets in Resources */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    lines.append("\t\t};")
    lines.append("/* End PBXResourcesBuildPhase section */")
    lines.append("")
    lines.append("/* Begin PBXSourcesBuildPhase section */")
    lines.append(f"\t\t{ids['sources_phase']} /* Sources */ = {{")
    lines.append("\t\t\tisa = PBXSourcesBuildPhase;")
    lines.append("\t\t\tbuildActionMask = 2147483647;")
    lines.append("\t\t\tfiles = (")
    for path in SOURCES:
        lines.append(f"\t\t\t\t{build_ids[path]} /* {Path(path).name} in Sources */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    lines.append("\t\t};")
    lines.append(f"\t\t{ids['test_sources_phase']} /* Sources */ = {{")
    lines.append("\t\t\tisa = PBXSourcesBuildPhase;")
    lines.append("\t\t\tbuildActionMask = 2147483647;")
    lines.append("\t\t\tfiles = (")
    for path in TESTS:
        lines.append(f"\t\t\t\t{build_ids[path]} /* {Path(path).name} in Sources */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\trunOnlyForDeploymentPostprocessing = 0;")
    lines.append("\t\t};")
    lines.append("/* End PBXSourcesBuildPhase section */")
    lines.append("")
    lines.append("/* Begin XCBuildConfiguration section */")

    def project_config(cid: str, name: str) -> None:
        lines.append(f"\t\t{cid} /* {name} */ = {{")
        lines.append("\t\t\tisa = XCBuildConfiguration;")
        lines.append("\t\t\tbuildSettings = {")
        lines.append("\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;")
        lines.append("\t\t\t\tCLANG_ENABLE_MODULES = YES;")
        lines.append("\t\t\t\tCOPY_PHASE_STRIP = NO;")
        lines.append("\t\t\t\tDEBUG_INFORMATION_FORMAT = dwarf;")
        lines.append("\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;")
        lines.append("\t\t\t\tGCC_DYNAMIC_NO_PIC = NO;")
        lines.append("\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 17.0;")
        lines.append("\t\t\t\tONLY_ACTIVE_ARCH = YES;")
        lines.append("\t\t\t\tSDKROOT = iphoneos;")
        lines.append("\t\t\t\tSWIFT_VERSION = 5.0;")
        if name == "Debug":
            lines.append("\t\t\t\tSWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;")
            lines.append("\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = \"-Onone\";")
        else:
            lines.append("\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;")
        lines.append("\t\t\t};")
        lines.append(f"\t\t\tname = {name};")
        lines.append("\t\t};")

    def app_config(cid: str, name: str) -> None:
        lines.append(f"\t\t{cid} /* {name} */ = {{")
        lines.append("\t\t\tisa = XCBuildConfiguration;")
        lines.append("\t\t\tbuildSettings = {")
        lines.append("\t\t\t\tASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;")
        lines.append("\t\t\t\tASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;")
        lines.append("\t\t\t\tCODE_SIGN_STYLE = Automatic;")
        lines.append("\t\t\t\tCURRENT_PROJECT_VERSION = 1;")
        lines.append("\t\t\t\tDEVELOPMENT_TEAM = \"\";")
        lines.append("\t\t\t\tENABLE_PREVIEWS = YES;")
        lines.append("\t\t\t\tENABLE_TESTABILITY = YES;")
        lines.append("\t\t\t\tGENERATE_INFOPLIST_FILE = YES;")
        lines.append("\t\t\t\tINFOPLIST_KEY_CFBundleDisplayName = \"Corner Empire\";")
        lines.append("\t\t\t\tINFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;")
        lines.append("\t\t\t\tINFOPLIST_KEY_UILaunchScreen_Generation = YES;")
        lines.append(
            "\t\t\t\tINFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone = "
            "\"UIInterfaceOrientationPortrait\";"
        )
        lines.append("\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (")
        lines.append("\t\t\t\t\t\"$(inherited)\",")
        lines.append("\t\t\t\t\t\"@executable_path/Frameworks\",")
        lines.append("\t\t\t\t);")
        lines.append("\t\t\t\tMARKETING_VERSION = 0.1.0;")
        lines.append("\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.example.IdleTycoon;")
        lines.append("\t\t\t\tPRODUCT_NAME = \"$(TARGET_NAME)\";")
        lines.append("\t\t\t\tSUPPORTED_PLATFORMS = \"iphoneos iphonesimulator\";")
        lines.append("\t\t\t\tSUPPORTS_MACCATALYST = NO;")
        lines.append("\t\t\t\tSWIFT_EMIT_LOC_STRINGS = YES;")
        lines.append("\t\t\t\tSWIFT_VERSION = 5.0;")
        lines.append("\t\t\t\tTARGETED_DEVICE_FAMILY = 1;")
        lines.append("\t\t\t};")
        lines.append(f"\t\t\tname = {name};")
        lines.append("\t\t};")

    def test_config(cid: str, name: str) -> None:
        lines.append(f"\t\t{cid} /* {name} */ = {{")
        lines.append("\t\t\tisa = XCBuildConfiguration;")
        lines.append("\t\t\tbuildSettings = {")
        lines.append("\t\t\t\tBUNDLE_LOADER = \"$(TEST_HOST)\";")
        lines.append("\t\t\t\tCODE_SIGN_STYLE = Automatic;")
        lines.append("\t\t\t\tCURRENT_PROJECT_VERSION = 1;")
        lines.append("\t\t\t\tGENERATE_INFOPLIST_FILE = YES;")
        lines.append("\t\t\t\tMARKETING_VERSION = 0.1.0;")
        lines.append("\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.example.IdleTycoonTests;")
        lines.append("\t\t\t\tPRODUCT_NAME = \"$(TARGET_NAME)\";")
        lines.append("\t\t\t\tSWIFT_VERSION = 5.0;")
        lines.append("\t\t\t\tTARGETED_DEVICE_FAMILY = 1;")
        lines.append(f"\t\t\t\tTEST_HOST = \"$(BUILT_PRODUCTS_DIR)/IdleTycoon.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/IdleTycoon\";")
        lines.append("\t\t\t};")
        lines.append(f"\t\t\tname = {name};")
        lines.append("\t\t};")

    project_config(ids["debug_project"], "Debug")
    project_config(ids["release_project"], "Release")
    app_config(ids["debug_app"], "Debug")
    app_config(ids["release_app"], "Release")
    test_config(ids["debug_test"], "Debug")
    test_config(ids["release_test"], "Release")
    lines.append("/* End XCBuildConfiguration section */")
    lines.append("")
    lines.append("/* Begin XCConfigurationList section */")
    lines.append(
        f"\t\t{ids['project_config_list']} /* Build configuration list for PBXProject \"IdleTycoon\" */ = {{"
    )
    lines.append("\t\t\tisa = XCConfigurationList;")
    lines.append("\t\t\tbuildConfigurations = (")
    lines.append(f"\t\t\t\t{ids['debug_project']} /* Debug */,")
    lines.append(f"\t\t\t\t{ids['release_project']} /* Release */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tdefaultConfigurationIsVisible = 0;")
    lines.append("\t\t\tdefaultConfigurationName = Release;")
    lines.append("\t\t};")
    lines.append(
        f"\t\t{ids['app_config_list']} /* Build configuration list for PBXNativeTarget \"IdleTycoon\" */ = {{"
    )
    lines.append("\t\t\tisa = XCConfigurationList;")
    lines.append("\t\t\tbuildConfigurations = (")
    lines.append(f"\t\t\t\t{ids['debug_app']} /* Debug */,")
    lines.append(f"\t\t\t\t{ids['release_app']} /* Release */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tdefaultConfigurationIsVisible = 0;")
    lines.append("\t\t\tdefaultConfigurationName = Release;")
    lines.append("\t\t};")
    lines.append(
        f"\t\t{ids['test_config_list']} /* Build configuration list for PBXNativeTarget \"IdleTycoonTests\" */ = {{"
    )
    lines.append("\t\t\tisa = XCConfigurationList;")
    lines.append("\t\t\tbuildConfigurations = (")
    lines.append(f"\t\t\t\t{ids['debug_test']} /* Debug */,")
    lines.append(f"\t\t\t\t{ids['release_test']} /* Release */,")
    lines.append("\t\t\t);")
    lines.append("\t\t\tdefaultConfigurationIsVisible = 0;")
    lines.append("\t\t\tdefaultConfigurationName = Release;")
    lines.append("\t\t};")
    lines.append("/* End XCConfigurationList section */")
    lines.append("\t};")
    lines.append(f"\trootObject = {ids['project']} /* Project object */;")
    lines.append("}")

    PROJECT.mkdir(parents=True, exist_ok=True)
    (PROJECT / "project.pbxproj").write_text("\n".join(lines) + "\n", encoding="utf-8")

    scheme_dir = PROJECT / "xcshareddata" / "xcschemes"
    scheme_dir.mkdir(parents=True, exist_ok=True)
    scheme = f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme
   LastUpgradeVersion = "1600"
   version = "1.7">
   <BuildAction
      parallelizeBuildables = "YES"
      buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "YES"
            buildForArchiving = "YES"
            buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{ids['app_target']}"
               BuildableName = "IdleTycoon.app"
               BlueprintName = "IdleTycoon"
               ReferencedContainer = "container:IdleTycoon.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      shouldUseLaunchSchemeArgsEnv = "YES"
      shouldAutocreateTestPlan = "YES">
      <Testables>
         <TestableReference
            skipped = "NO"
            parallelizable = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{ids['test_target']}"
               BuildableName = "IdleTycoonTests.xctest"
               BlueprintName = "IdleTycoonTests"
               ReferencedContainer = "container:IdleTycoon.xcodeproj">
            </BuildableReference>
         </TestableReference>
      </Testables>
   </TestAction>
   <LaunchAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      launchStyle = "0"
      useCustomWorkingDirectory = "NO"
      ignoresPersistentStateOnLaunch = "NO"
      debugDocumentVersioning = "YES"
      debugServiceExtension = "internal"
      allowLocationSimulation = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{ids['app_target']}"
            BuildableName = "IdleTycoon.app"
            BlueprintName = "IdleTycoon"
            ReferencedContainer = "container:IdleTycoon.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction
      buildConfiguration = "Release"
      shouldUseLaunchSchemeArgsEnv = "YES"
      savedToolIdentifier = ""
      useCustomWorkingDirectory = "NO"
      debugDocumentVersioning = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{ids['app_target']}"
            BuildableName = "IdleTycoon.app"
            BlueprintName = "IdleTycoon"
            ReferencedContainer = "container:IdleTycoon.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction
      buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction
      buildConfiguration = "Release"
      revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>
"""
    (scheme_dir / "IdleTycoon.xcscheme").write_text(scheme, encoding="utf-8")
    print(f"Wrote {PROJECT}")


if __name__ == "__main__":
    main()
