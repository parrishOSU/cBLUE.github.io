#import laspy
#from collections import OrderedDict

#xy_data_type = 7 # 10 = laspy unsigned long long (8 bytes)
#z_data_type = 5 # 5 = laspy unsigned long (4 bytes)
#tpu_data_type = 5

#extra_byte_dimensions = OrderedDict([
#    ('cblue_x', ('calculated x', xy_data_type)),
#    ('cblue_y', ('calculated y', xy_data_type)),
#    ('cblue_z', ('calculated z', z_data_type)),
#    ('subaerial_thu', ('subaerial thu', tpu_data_type)),
#    ('subaerial_tvu', ('subaerial tvu', tpu_data_type)),
#    ('subaqueous_thu', ('subaqueous thu', tpu_data_type)),
#    ('subaqueous_tvu', ('subaqueous tvu', tpu_data_type)),
#    ('total_thu', ('total thu', tpu_data_type)),
#    ('total_tvu', ('total tvu', tpu_data_type))
#    ])

## Set up our input and output files.
#inFile =
#laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2870000n_TPU.las",
#mode = "r")

#headerformat = inFile.header.header_format
#for spec in headerformat:
#    print(spec.name)
    
#point_records = inFile.points
#print(point_records)


#print inFile.header.evlrs

#for dim in inFile.reader.point_format:
#    print('{:20s}: {}'.format(dim.name,
#    inFile.reader.get_dimension(dim.name)))


#for vlr in inFile.header.vlrs:
#    print vlr.parsed_body


import laspy
import copy
import codecs


inFile = laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2870000n.las", mode="r")

# We need to build the body of our dimension VLRs, and to do this we
# will use a class called ExtraBytesStruct.  All we really need to tell
# it at this point is the name of our dimension and the data type.
extra_dim_spec_1 = laspy.header.ExtraBytesStruct(
    name="tpu_thu",
    data_type = 5,
    scale=[0.001, 0.001, 0.001])
extra_dim_spec_2 = laspy.header.ExtraBytesStruct(
    name="tpu_tvu",
    data_type = 5,
    scale=[0.001, 0.001, 0.001])

vlr_body = (extra_dim_spec_1.to_byte_string() + extra_dim_spec_2.to_byte_string())

# Now we can create the VLR.  Note the user_id and record_id choices.
# These values are how the LAS specification determines that this is an
# extra bytes record.  The description is just good practice.
extra_dim_vlr = laspy.header.VLR(user_id = "LASF_Spec",
    record_id = 4,
    description = "cblue_tpu",
    VLR_body = vlr_body)

# Now let's put together the header for our new file.  We need to increase
# data_record_length to fit our new dimensions.  See the data_type table
# for details.  We also need to change the file version
new_header = copy.copy(inFile.header)
new_header.data_record_length += 8
new_header.format = 1.4

# Now we can create the file and give it our VLR.
new_file = laspy.file.File(r"C:\QAQC_contract\marco_island\2016_429500e_2870000n_TPU.las", mode = "w",
header = new_header, vlrs = [extra_dim_vlr])

# Let's copy the existing data:
for dimension in inFile.point_format:
    dim = inFile._reader.get_dimension(dimension.name)
    new_file._writer.set_dimension(dimension.name, dim)

# We should be able to acces our new dimensions based on the
# Naming convention described above.  Let's put some dummy data in them.
new_file.tpu_thu = [0] * len(new_file)
new_file.tpu_tvu = [10] * len(new_file)

headerformat = new_file.header.header_format
print new_file.header.get_global_encoding()

for spec in headerformat:
    print(spec.name, new_file.header.reader.get_header_property(spec.name))

for dim in new_file.reader.point_format:
    print('{:20s}: {}'.format(dim.name, new_file.reader.get_dimension(dim.name)))

print new_file.extra_bytes

#for vlr in new_file.header.vlrs:
#    print vlr.scale

