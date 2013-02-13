#include <stdlib.h>
#include <stdio.h>
#include <sched.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <string.h>

#ifndef CLONE_NEWNS
#define CLONE_NEWNS 0x00020000
#endif


char* apps_dest_dir = "/usr/local/whack";
char* apps_bin_dir = "/usr/local/whack/bin";
        
int unshare_mount_namespace() {
    return syscall(__NR_unshare, CLONE_NEWNS);
}

int directory_exists(char* path) {
    struct stat st;
    return stat(path, &st) == 0;
}

int ensure_apps_dest_dir_exists() {
    if (directory_exists(apps_dest_dir)) {
        return 0;
    } else {
        return mkdir(apps_dest_dir, 0755);
    }
}

int mount_bind(char* src_path, char* dest_path) {
    return mount(src_path, dest_path, NULL, MS_BIND, NULL);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <apps-dir> <app> <args>\n", argv[0]);
        return 1;
    }
    if (unshare_mount_namespace() != 0) {
        printf("ERROR: Could not unshare mount namespace\n");
        return 1;
    }
    if (ensure_apps_dest_dir_exists() != 0) {
        printf("ERROR: Could not create %s\n", apps_dest_dir);
        return 1;
    }
    char* apps_src_dir = argv[1];
    if (mount_bind(apps_src_dir, apps_dest_dir) != 0) {
        printf("ERROR: Could not mount %s\n", apps_src_dir);
        return 1;
    }
    
    if (chown(apps_dest_dir, getuid(), getgid()) != 0) {
        printf("ERROR: Could not chown %s\n", apps_dest_dir);
        return 1;
    }
    
    if (setgid(getgid()) != 0) {
        printf("ERROR: Could not drop group privileges");
        return 1;
    }
    if (setuid(getuid()) != 0) {
        printf("ERROR: Could not drop user privileges");
        return 1;
    }
    
    char* app = argv[2];
    char** app_args = (char**)malloc(sizeof(char*) * (argc - 1));
    for (int i = 2; i < argc; i++) {
        app_args[i - 2] = argv[i];
    }
    app_args[argc - 2] = 0;
    char* original_path = getenv("PATH");
    char* new_path = (char*)malloc(sizeof(char) * strlen(original_path) + strlen(apps_bin_dir) + strlen(":") + 1);
    sprintf(new_path, "%s:%s", apps_bin_dir, original_path);
    setenv("PATH", new_path, 1);
    
    if (execvp(app, app_args) != 0) {
        printf("ERROR: failed to exec %s\n", app);
        return 1;
    }
    
    return 2;
}
