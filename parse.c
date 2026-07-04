#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

#define BUF_SIZE 320

FILE *current_file = NULL;

/* XOR-based encryption (not the most secure)*/
#define ROOT 0xAA
void xor_crypt(char *dst, const char *src, size_t n) {
    for (int i = 0; i < n; i++) {
        dst[i] = src[i] ^ (ROOT+i);
    }
}

int main(void) {
    char buf[BUF_SIZE] = {0};
    char input_val[96];
    char tmp[32];
    char io_buf[192];
    char out_buf[192];

    ssize_t n = read(STDIN_FILENO, buf, BUF_SIZE - 1);
    if (n <= 0)
        return 0;

    /// check if stdin is in the right format
    char *cmd   = strstr(buf, "CMD:");
    char *input = strstr(buf, "INPUT:");
    char *mode  = strstr(buf, "MODE:");

    if (!cmd || !input || !mode)
        return 0;
        
    int colon_count = 0;
    int comma_count = 0;
    
    for(ssize_t i=0; i<n; i++){
        if(buf[i] == ':') colon_count++;
        else if(buf[i] == ',') comma_count++;
    }

    if(colon_count != 3 || comma_count != 2){
        printf("Invalid format\n");
        return 0;
    }

    cmd   += 4;
    if (strncmp(cmd, "WRITE", 5) != 0 && strncmp(cmd, "READ", 4) != 0)
    {
    	printf("Invalid CMD\n");
    	return 0;
    }

    mode  += 5;
    if (strncmp(mode, "BASIC", 5) != 0 && strncmp(mode, "ENC", 3) != 0)
    {
        printf("Invalid MODE\n");
        return 0;
    }
    
    input += 6;
    char* input_end = strchr(input, ',');
    if(!input_end)
        return 0;
        
    size_t input_len = input_end - input;
    if(input_len >= sizeof(input_val))
        input_len = sizeof(input_val)-1;
    memcpy(input_val, input, input_len);
    input_val[input_len] = '\0';

    /// Process the WRITE command
    if (strncmp(cmd, "WRITE", 5) == 0) {
    	/// If write, check input contains valid string chars
    	for (size_t i = 0; i < input_len; i++) {
	    if (!(
               (input_val[i] >= '0' && input_val[i] <= '9') ||
		       (input_val[i] >= 'a' && input_val[i] <= 'z') ||
		       (input_val[i] >= 'A' && input_val[i] <= 'Z')
             )
            )
            printf("Invalid char %d\n", input_val[i]);
		return 0;
	}

	   current_file = fopen("data.txt", "w+");

        strcpy(tmp, input_val); 
	
        if (strncmp(mode, "BASIC", 5) == 0) {
            printf("Writing %s to 'data.txt'...\n", input_val);
            fprintf(current_file, "%s", tmp);
        }
        else if (strncmp(mode, "ENC", 3) == 0) {
            printf("Encrypting...\n");
            xor_crypt(out_buf, tmp, strlen(tmp));
            printf("Writing to file...\n");
            fwrite(out_buf, 1, strlen(tmp), current_file);
        }
    }

    /// Process the READ command
    else if (strncmp(cmd, "READ", 4) == 0) {
	current_file = fopen("data.txt", "r+");
	/// If int is negative, set to 0
        int count = atoi(input_val);
	if(count < 0){
	    count = 0;
	}
        fseek(current_file, 0, SEEK_SET);
        size_t r = fread(io_buf, 1, count, current_file);

        if (strncmp(mode, "BASIC", 5) == 0) {
            printf("Reading: %s\n",io_buf);
        }
        else if (strncmp(mode, "ENC", 3) == 0) {
            printf("Decrypting %s...\n",io_buf);
            xor_crypt(out_buf, io_buf, r);
            printf("Reading: %s\n",out_buf);
        }
    }

    printf("Done\n");
	
    return 0;
}
