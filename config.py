overwrite_existing = False
save_path = r""
save_full_text = True

# Authentication details
uid = ""
hsh = ""

# AVAILABLE FIELDS
#  name
#  post_date
#  post_id
#  desc
#  photo_seq (do not change this)
#  ext (do not change this)

file_name_format = '{post_date}_{desc}{photo_seq}.{ext}'

# PROBABLY DON'T NEED TO CHANGE THIS
api_url = 'https://justfor.fans/ajax/getPosts.php?UserID={userid}&Type=All&StartAt={seq}&Source=Home&UserHash4={hash}'


# for debugging purposes

VERBOSE = True

if __name__ == "__main__":
    print(api_url.format(userid=uid, hash=hsh, seq=0))