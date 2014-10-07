sudo chown root:wheel g13.kext
sudo cp -r g13.kext /System/Library/Extensions/g13.kext
sudo touch /System/Library/Extensions
sudo kextload -vt /System/Library/Extensions/g13.kext
