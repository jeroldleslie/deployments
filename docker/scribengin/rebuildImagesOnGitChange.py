#Rebuild images if a file from the last check in contains the string "docker" (i.e. the docker folder was updated)
import subprocess,re, os, shutil
p = subprocess.Popen(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
out, err = p.communicate()
rebuild=False
for filename in out.split():
  if re.search( "docker" ,filename):
    rebuild=True

if rebuild:
  thisFilesDir = os.path.dirname(os.path.realpath(__file__))
  neverwinterdpHome = os.path.join(thisFilesDir, "NeverwinterDP")
  
  os.chdir(thisFilesDir)
  
  print "Cloning NeverwinterDP..."
  p = subprocess.Popen(['git', 'clone','https://github.com/Nventdata/NeverwinterDP'],
                                stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
  out, err = p.communicate()
  print "STDERR: "+err
  print "STDOUT: "+out
  
  print "\nRebuilding Images..."
  p = subprocess.Popen(['./docker.sh', 'cluster','--clean-containers','--clean-image',
                        '--build-image', '--ansible-inventory', '--deploy',
                        '--neverwinterdp-home='+neverwinterdpHome],
                        stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
  out, err = p.communicate()
  print "STDERR: "+err
  print "STDOUT: "+out
  
  print "Deleting "+neverwinterdpHome
  shutil.rmtree(neverwinterdpHome)
  
else:
  print "No rebuild required"
  