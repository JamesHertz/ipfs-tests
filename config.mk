# this is used to generate .ipfs-env
# install for dotenv: pip install "python-dotenv[cli]"

TARGET := .ipfs-env
DEPS   := .env
all:  $(TARGET)

$(TARGET): $(DEPS)
	dotenv -f $< list > $@